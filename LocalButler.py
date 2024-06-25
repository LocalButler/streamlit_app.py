import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from pathlib import Path
import bcrypt
import os
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd

# Define the function to get booked slots
def get_booked_slots(df_bookings, selected_date):
    booked_slots = []
    try:
        for index, row in df_bookings.iterrows():
            date = row['Date']
            time = row['Time']
            
            if date == selected_date:
                booked_slots.append(time)
    except Exception as e:
        print(f"Error occurred: {e}")
    
    return booked_slots

# Example of loading data from a CSV file
def load_bookings_data():
    df_bookings = pd.read_csv('bookings.csv')  # Replace with your actual CSV file path
    return df_bookings

# Function to display calendar
def display_calendar():
    st.subheader("Calendar")

    # Example: Select a date (replace with your actual date selection logic)
    selected_date_str = st.date_input("Select a date", datetime.now().date())
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    # Get booked slots for the selected date
    booked_slots = get_booked_slots(df_bookings, selected_date)

    # Display booked slots
    if booked_slots:
        st.write(f"Booked slots for {selected_date}: {booked_slots}")
    else:
        st.write(f"No booked slots for {selected_date}")

# Database setup
DB_FILE = "users.db"
db_path = Path(DB_FILE)
if not db_path.exists():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            failed_attempts INTEGER DEFAULT 0,
            last_attempt TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Database functions
def get_db_connection():
    return sqlite3.connect(DB_FILE)

def insert_user(username, password):
    with get_db_connection() as conn:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def authenticate_user(username, password):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password, failed_attempts, last_attempt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            stored_password, failed_attempts, last_attempt = user
            if last_attempt:
                last_attempt = datetime.fromisoformat(last_attempt)
                if last_attempt + timedelta(minutes=15) > datetime.now() and failed_attempts >= 5:
                    return False, "Account locked. Try again later."
            
            if bcrypt.checkpw(password.encode(), stored_password):
                cursor.execute("UPDATE users SET failed_attempts = 0, last_attempt = NULL WHERE username = ?", (username,))
                conn.commit()
                return True, "Login successful"
            else:
                cursor.execute("UPDATE users SET failed_attempts = failed_attempts + 1, last_attempt = ? WHERE username = ?", 
                               (datetime.now().isoformat(), username))
                conn.commit()
                return False, "Invalid username or password"
        return False, "Invalid username or password"

# Decorators
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get('logged_in'):
            st.warning("Please log in to access this feature.")
            return
        return func(*args, **kwargs)
    return wrapper

# Service data
GROCERY_STORES = {
    "Weis Markets": {
        "url": "https://www.weismarkets.com/",
        "video_url": "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/1ff75ee91b2717fabadb44ee645612d6e48e8ee3/Weis%20Promo%20Online%20ordering%20%E2%80%90.mp4",
        "video_title": "Watch this video to learn how to order from Weis Markets:",
        "instructions": [
            "Place your order directly with Weis Markets using your own account to accumulate grocery store points and clip your favorite coupons.",
            "Select store pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "SafeWay": {
        "url": "https://www.safeway.com/",
        "instructions": [
            "Place your order directly with Safeway using your own account to accumulate grocery store points and clip your favorite coupons.",
            "Select store pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ],
        "image_url": "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/main/safeway%20app%20ads.png"
    },
    "Commissary": {
        "url": "https://shop.commissaries.com/",
        "instructions": [
            "Place your order directly with the Commissary using your own account.",
            "Select store pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ],
        "image_url": "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/main/comissaries.jpg"
    },
    "Food Lion": {
        "url": "https://shop.foodlion.com/?shopping_context=pickup&store=2517",
        "instructions": [
            "Place your order directly with Food Lion using your own account.",
            "Select store pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ],
        "image_url": "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/main/foodlionhomedelivery.jpg"
    }
}

RESTAURANTS = {
    "The Hideaway": {
        "url": "https://order.toasttab.com/online/hideawayodenton",
        "instructions": [
            "Place your order directly with The Hideaway using their website or app.",
            "Select pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ],
        "image_url": "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/main/TheHideAway.jpg"
    },
    "Ruth's Chris Steak House": {
        "url": "https://order.ruthschris.com/",
        "instructions": [
            "Place your order directly with Ruth's Chris Steak House using their website or app.",
            "Select pick-up and specify the date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Baltimore Coffee & Tea Company": {
        "url": "https://www.baltcoffee.com/sites/default/files/pdf/2023WebMenu_1.pdf",
        "instructions": [
            "Review the menu and decide on your order.",
            "Call Baltimore Coffee & Tea Company to place your order.",
            "Specify that you'll be using Local Butler for pick-up and delivery.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!",
            "We apologize for any inconvenience, but Baltimore Coffee & Tea Company does not currently offer online ordering."
        ]
    },
    "The All American Steakhouse": {
        "url": "https://order.theallamericansteakhouse.com/menu/odenton",
        "instructions": [
            "Place your order directly with The All American Steakhouse by using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Jersey Mike's Subs": {
        "url": "https://www.jerseymikes.com/menu",
        "instructions": [
            "Place your order directly with Jersey Mike's Subs using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Bruster's Real Ice Cream": {
        "url": "https://brustersonline.com/brusterscom/shoppingcart.aspx?number=415&source=homepage",
        "instructions": [
            "Place your order directly with Bruster's Real Ice Cream using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Luigino's": {
        "url": "https://order.yourmenu.com/luiginos",
        "instructions": [
            "Place your order directly with Luigino's by using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "PHO 5UP ODENTON": {
        "url": "https://www.clover.com/online-ordering/pho-5up-odenton",
        "instructions": [
            "Place your order directly with PHO 5UP ODENTON by using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Dunkin": {
        "url": "https://www.dunkindonuts.com/en/mobile-app",
        "instructions": [
            "Place your order directly with Dunkin' by using their APP.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    },
    "Baskin-Robbins": {
        "url": "https://order.baskinrobbins.com/categories?storeId=BR-339568",
        "instructions": [
            "Place your order directly with Baskin-Robbins by using their website or app.",
            "Specify the items you want to order and the pick-up date and time.",
            "Let Butler Bot know you've placed a pick-up order, and we'll take care of the rest!"
        ]
    }
}

# Service display functions
@login_required
def display_grocery_services():
    st.write("Order fresh groceries from your favorite local stores and have them delivered straight to your doorstep.")
    
    video_url = "https://raw.githubusercontent.com/LocalButler/streamlit_app.py/119398d25abc62218ccaec71f44b30478d96485f/Local%20Butler%20Groceries.mp4"
    
    video_html = f"""
        <div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%;">
            <video autoplay loop muted playsinline
                style="position: absolute; top: -25%; left: 0; width: 100%; height: 125%;"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                <source src="{video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div style="position: absolute; top: -5%; left: 0; width: 100%; height: 92%; background-color: black; opacity: 0.3;"></div>
        </div>
    """
    components.html(video_html, height=315)

    grocery_store = st.selectbox("Choose a store:", list(GROCERY_STORES.keys()))
    store_info = GROCERY_STORES[grocery_store]
    st.write(f"ORDER NOW: [{grocery_store}]({store_info['url']})")
    
    if "video_url" in store_info:
        st.markdown(f"### {store_info['video_title']}")
        store_video_html = f"""
            <div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%;">
                <video autoplay playsinline controls
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                    <source src="{store_info['video_url']}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
        """
        components.html(store_video_html, height=315)
    elif "image_url" in store_info:
        st.image(store_info['image_url'], caption=f"{grocery_store} App", use_column_width=True)
    
    st.write("Instructions for placing your order:")
    for instruction in store_info["instructions"]:
        st.write(f"- {instruction}")

@login_required
def display_meal_delivery_services():
    st.write("Enjoy delicious meals from top restaurants in your area delivered to your home or office.")
    restaurant = st.selectbox("Choose a restaurant:", list(RESTAURANTS.keys()))
    restaurant_info = RESTAURANTS[restaurant]
    st.write(f"ORDER NOW: [{restaurant}]({restaurant_info['url']})")
    st.write("Instructions for placing your order:")
    for instruction in restaurant_info["instructions"]:
        st.write(f"- {instruction}")

def display_about_us():
    st.write("Local Butler is a dedicated concierge service aimed at providing convenience and peace of mind to residents of Fort Meade, Maryland 20755. Our mission is to simplify everyday tasks and errands, allowing our customers to focus on what matters most.")

def display_how_it_works():
    st.write("1. Choose a service category from the menu.")
    st.write("2. Select your desired service.")
    st.write("3. Follow the prompts to complete your order.")
    st.write("4. Sit back and relax while we take care of the rest!")

@login_required
def display_new_order():
    iframe_html = """
    <iframe title="Pico embed" src="https://a.picoapps.xyz/shoulder-son?utm_medium=embed&utm_source=embed" width="98%" height="680px" style="background:white"></iframe>
    """
    components.html(iframe_html, height=680)


def display_calendar():
    st.subheader("Calendar")
    
    # Select a date to view available slots
    selected_date = st.date_input("Select a date", min_value=datetime.today())
    
    # Display available time slots for the selected date
    display_available_time_slots(selected_date)


def display_available_time_slots(selected_date):
    st.subheader(f"Available Time Slots for {selected_date.strftime('%Y-%m-%d')}")
    
    # Assume df_bookings is defined somewhere in your code
    # Example: df_bookings = pd.DataFrame(columns=['Date', 'Time', 'User'])
    
    # Generate all possible time slots for the selected date (9:00 AM to 6:00 PM, every 30 minutes)
    all_slots = pd.date_range(start=f"{selected_date} 09:00", end=f"{selected_date} 18:00", freq="30min")
    
    # Filter out booked slots
    booked_slots = get_booked_slots(selected_date)
    available_slots = [slot.time() for slot in all_slots if slot.time() not in booked_slots]
    
    if available_slots:
        st.write("Available slots:")
        for slot in available_slots:
            st.write(slot.strftime("%I:%M %p"))
    else:
        st.write("No available slots for this date.")

def get_booked_slots(selected_date):
    # Function to retrieve booked slots from df_bookings for the selected date
    # Example: Replace with your actual logic to fetch booked slots from a database or dataframe
    booked_slots = []
    # Assuming df_bookings is a global dataframe containing booked slots
    for index, row in df_bookings.iterrows():
        if row['Date'] == selected_date:
            booked_slots.append(row['Time'].time())
    return booked_slots

def main():
    st.set_page_config(page_title="Local Butler")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ''

    menu = ["Home", "Menu", "Order", "Butler Bot", "Calendar", "About Us", "Login"]
    if st.session_state['logged_in']:
        menu.append("Logout")
    else:
        menu.append("Register")

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Welcome to Local Butler!")
        st.write("Please navigate through the sidebar to explore our app.")

    elif choice == "Menu":
        st.subheader("Menu")
        with st.expander("Service Categories", expanded=False):
            category = st.selectbox("Select a service category:", ("Grocery Services", "Meal Delivery Services"))
            if category == "Grocery Services":
                display_grocery_services()
            elif category == "Meal Delivery Services":
                display_meal_delivery_services()

    elif choice == "Order":
        if st.session_state['logged_in']:
            st.subheader("Order")
            st.write("Order functionality coming soon!")
        else:
            st.warning("Please log in to place an order.")

    elif choice == "Butler Bot":
        st.subheader("Butler Bot")
        display_new_order()

    elif choice == "Calendar":
        st.subheader("Calendar")
        display_calendar()

    elif choice == "About Us":
        st.subheader("About Us")
        display_about_us()
        display_how_it_works()

    elif choice == "Login":
        if not st.session_state['logged_in']:
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    success, message = authenticate_user(username, password)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
        else:
            st.warning("You are already logged in.")

    elif choice == "Logout":
        if st.session_state['logged_in']:
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.session_state['username'] = ''
                st.success("Logged out successfully!")
                st.experimental_rerun()
        else:
            st.warning("You are not logged in.")

    elif choice == "Register":
        st.subheader("Register")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')
        if st.button("Register"):
            if not new_username or not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                if insert_user(new_username, new_password):
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error("Username already exists. Please choose a different username.")

if __name__ == "__main__":
    main()
