from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from geopy.distance import geodesic
from auth_gspread import get_sheet
import logging
import osmnx as ox
import networkx as nx
from staticmap import StaticMap, CircleMarker, Line
from PIL import Image
from io import BytesIO
import requests
import io
import os
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SHEET_NAME = "Tsel Bot"
sheet = get_sheet(SHEET_NAME)

user_locations = {}  # Simpan lokasi pengguna
user_states = {}     # Simpan status pengguna

def get_all_tasks():
    return sheet.get_all_records()

def update_task(index, data):
    for key, value in data.items():
        sheet.update_cell(index + 2, get_column_index(key), value)

def get_column_index(col_name):
    header = sheet.row_values(1)
    return header.index(col_name) + 1


def get_osrm_distance_duration(origin, destination):
    base_url = "http://router.project-osrm.org/route/v1/driving/"
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    params = {"overview": "false"}
    
    try:
        response = requests.get(base_url + coords, params=params)
        data = response.json()
        if 'routes' in data and data['routes']:
            route = data['routes'][0]
            distance_km = round(route['distance'] / 1000, 2)
            duration_min = round(route['duration'] / 60, 1)
            return distance_km, duration_min
    except Exception as e:
        print(f"OSRM error: {e}")

    return None, None

def find_nearest_task(location, tasks):
    min_distance = float('inf')
    nearest_task = None

    for idx, task in enumerate(tasks):
        if task['status'].lower() == 'available':
            try:
                distance_km, duration_min = get_osrm_distance_duration(location, (task['lat'], task['lon']))
                if distance_km is not None and distance_km < min_distance:
                    min_distance = distance_km
                    nearest_task = (idx, task, distance_km, duration_min)
            except:
                continue

    return nearest_task

keyboard_main = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔍 Search Task", callback_data='search_task')],
    [InlineKeyboardButton("ℹ️ Task Info", callback_data='task_info'), InlineKeyboardButton("📍 Where", callback_data='where'), InlineKeyboardButton("❓ Help", callback_data='help')],
])

keyboard_take = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Take Task", callback_data='take_task')],
])

keyboard_on_task = InlineKeyboardMarkup([
    [InlineKeyboardButton("❌ Cancel", callback_data='cancel'), InlineKeyboardButton("🧭 Go", callback_data='go')],
    [InlineKeyboardButton("ℹ️ Task Info", callback_data='task_info'), InlineKeyboardButton("📍 Where", callback_data='where'), InlineKeyboardButton("❓ Help", callback_data='help')],
])

keyboard_working = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Done", callback_data='done')],
    [InlineKeyboardButton("ℹ️ Task Info", callback_data='task_info'), InlineKeyboardButton("📍 Where", callback_data='where'), InlineKeyboardButton("❓ Help", callback_data='help')],
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Selamat datang teknisi! Silakan pilih opsi:", reply_markup=keyboard_main)

async def help_command(update_or_query, context):
    help_text = (
        "/start - Mulai\n"
        "🔍 Search Task - Cari tugas terdekat\n"
        "ℹ️ Task Info - Info tugas aktif\n"
        "📍 Where - Lokasi Anda sekarang\n"
        "❌ Cancel - Batalkan tugas\n"
        "🧭 Go - Navigasi ke tugas\n"
        "✅ Done - Tandai tugas selesai"
    )
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(help_text)
    else:
        await update_or_query.edit_message_text(help_text)

async def where(update_or_query, context):
    user_id = update_or_query.from_user.id
    loc = user_locations.get(user_id)
    text = f"Lokasi Anda: {loc[0]}, {loc[1]}" if loc else "Lokasi belum tersedia. Kirim lokasi dulu ya."
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text)
    else:
        await update_or_query.edit_message_text(text)

async def task_info(update_or_query, context):
    chat_id = str(update_or_query.from_user.id)
    tasks = get_all_tasks()
    available_count = sum(1 for t in tasks if t['status'].lower() == 'available')
    for task in tasks:
        if task['assigned_to'] == chat_id and task['status'].lower() in ['keep', 'working']:
            text = (
                f"📝 Tugas: {task['order_id']}\n"
                f"📍 Lokasi: {task['lat']}, {task['lon']}\n"
                f"📌 Status: {task['status']}\n"
                f"Tugas tersedia: {available_count}"
            )
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(text)
            else:
                await update_or_query.edit_message_text(text)
            return
    text = f"Tidak ada tugas aktif.\nTugas tersedia: {available_count}"
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text)
    else:
        await update_or_query.edit_message_text(text)


def generate_static_map(user_loc, task_loc):
    # Hitung bounding box dari user dan task
    min_lat = min(user_loc[0], task_loc[0])
    max_lat = max(user_loc[0], task_loc[0])
    min_lon = min(user_loc[1], task_loc[1])
    max_lon = max(user_loc[1], task_loc[1])

    # Tambahkan margin sedikit agar marker tidak mepet pinggir
    margin = 0.01
    min_lat -= margin
    max_lat += margin
    min_lon -= margin
    max_lon += margin

    # Marker Geoapify
    user_marker = f"lonlat:{user_loc[1]},{user_loc[0]};type:awesome;color:blue;icon:user"
    task_marker = f"lonlat:{task_loc[1]},{task_loc[0]};type:awesome;color:red;icon:flag"

    api_key = os.getenv("GEOAPIFY_API")
    if not api_key:
        raise RuntimeError("MAPS_API_KEY tidak ditemukan di environment variables")

    # Gunakan bounding box agar zoom otomatis
    url = (
        f"https://maps.geoapify.com/v1/staticmap?"
        f"style=osm-bright&"
        f"bbox={min_lon},{min_lat},{max_lon},{max_lat}&"
        f"size=600x400&"
        f"marker={user_marker}&marker={task_marker}&"
        f"apiKey={api_key}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"Map request failed: {response.status_code}")

    output = io.BytesIO(response.content)
    output.seek(0)
    return output


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = str(user_id)

    # Cek dulu apakah user punya tugas aktif
    tasks = get_all_tasks()
    user_task = next((t for t in tasks if t['assigned_to'] == chat_id and t['status'].lower() in ['keep', 'working']), None)
    if user_task:
        idx_task = tasks.index(user_task)
        user_states[user_id] = {'task_idx': idx_task}
        await update.message.reply_text("🚫 Kamu masih punya tugas aktif. Selesaikan dulu ya.", reply_markup=keyboard_on_task)
        return

    user_loc = (update.message.location.latitude, update.message.location.longitude)
    user_locations[user_id] = user_loc
    await update.message.reply_text("Lokasi diterima. Mencari tugas terdekat...")

    nearest = find_nearest_task(user_loc, tasks)
    if not nearest:
        await update.message.reply_text("Tidak ada tugas tersedia saat ini.")
        return

    idx_task, task, distance_km, duration_min = nearest
    user_states[user_id] = {'task_idx': idx_task}

    image = generate_static_map(user_loc, (task['lat'], task['lon']))
    await update.message.reply_photo(photo=image)
    await update.message.reply_text(
       f"🎯 Tugas ditemukan: {task['order_id']}\n"
        f"📍 Estimasi jarak: {distance_km:.1f} km\n"
        # f"⏱️ Estimasi waktu: {duration_min:.1f} menit\n"
        f"Ambil tugas ini?",
        reply_markup=keyboard_take
    )   

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    chat_id = str(user_id)

    tasks = get_all_tasks()

    if data == "search_task":
      # Cek apakah user sudah punya tugas aktif
      tasks = get_all_tasks()  # Pastikan refresh data
      user_task = next((t for t in tasks if t['assigned_to'] == user_id and t['status'].lower() in ['keep', 'working']), None)
      # print(type(tasks['assigned_to']))
      
      if user_task:
          # Update user_states agar sinkron
          user_states[user_id] = {'task_idx': tasks.index(user_task)}
          await query.message.reply_text("🚫 Kamu masih punya tugas aktif. Selesaikan dulu sebelum ambil tugas lain.", reply_markup=keyboard_on_task)
          return

      available_tasks = [t for t in tasks if t['status'].lower() == 'available']
      if not available_tasks:
          await query.message.reply_text("🚫 Tidak ada tugas tersedia saat ini.", reply_markup=keyboard_main)
      else:
          await query.message.reply_text(
              "✅ Tugas tersedia ditemukan. Silakan kirim lokasi kamu terlebih dahulu.",
              reply_markup=ReplyKeyboardMarkup(
                  [[KeyboardButton("📍 Kirim Lokasi", request_location=True)]],
                  resize_keyboard=True,
                  one_time_keyboard=True
              )
          )

    
    elif data == "take_task":
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("Tugas tidak ditemukan. Silakan ulangi.")
            return
        idx = state['task_idx']
        tasks = get_all_tasks()  # Refresh
        if tasks[idx]['status'].lower() != 'available':
            await query.message.reply_text("Maaf, tugas sudah diambil orang lain. Coba cari lagi.", reply_markup=keyboard_main)
            return
        update_task(idx, {"status": "keep", "assigned_to": chat_id})
        await query.message.reply_text("Tugas berhasil diambil. Siap menuju lokasi!", reply_markup=keyboard_on_task)

    elif data == "go":
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("Tidak ada tugas aktif.")
            return
        update_task(state['task_idx'], {"status": "working"})
        await query.message.reply_text("Status tugas diubah menjadi 'working'. Silakan kerjakan!", reply_markup=keyboard_working)

    elif data == "cancel":
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("Tidak ada tugas untuk dibatalkan.")
            return
        update_task(state['task_idx'], {"status": "available", "assigned_to": ""})
        user_states.pop(user_id, None)
        await query.message.reply_text("Tugas dibatalkan. Silakan cari tugas lain.", reply_markup=keyboard_main)

    elif data == "done":
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("Tidak ada tugas aktif.")
            return
        update_task(state['task_idx'], {"status": "done"})
        user_states.pop(user_id, None)
        count = sum(1 for t in get_all_tasks() if t['status'].lower() == 'available')
        await query.message.reply_text(f"Tugas selesai! ✅\nTugas yang masih tersedia: {count}", reply_markup=keyboard_main)

    elif data == "task_info":
        await task_info(query, context)

    elif data == "help":
        await help_command(query, context)

    elif data == "where":
        await where(query, context)

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.LOCATION, location_handler))
app.add_handler(CommandHandler("help", help_command))

app.run_polling()
