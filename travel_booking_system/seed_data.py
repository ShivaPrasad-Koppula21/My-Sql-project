"""
TRAVELNEST Seed Data Generation Script
Generates a comprehensive, relational dataset with:
- 20 User Accounts (1 Admin, 19 Customers)
- 60 Destinations (Indian & International)
- 150 Hotels + Hotel Room inventories
- 500 Flight records across multiple routes and classes
- 100 Curated Travel Packages
- 200 Activities & Excursions
- 100 User Trip Plans
- 300 Realistic Bookings
- 150 User Reviews

Exports all data to relational database and CSV files in data/ directory.
"""

import os
import sys
import random
import datetime
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BASE_DIR
from database import init_db, execute_query, fetch_one, execute_commit, get_backend_type
from auth import generate_salt, hash_password
from utils.helpers import generate_booking_reference

# Fix seed for determinism and repeatability
random.seed(42)

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


# ========================================================
# 1. CORE DATA CONSTANTS
# ========================================================

DESTINATIONS_DATA = [
    # Indian Destinations (35)
    ("Goa", "Panaji", "India", "Beach", "Golden beaches, vibrant nightlife, Portuguese colonial architecture and coastal cuisine.", "Nov - Feb", 18000, "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80", 4.7, 1),
    ("Jaipur", "Jaipur", "India", "Heritage", "The Pink City featuring majestic Amber Fort, City Palace, and rich Rajasthani heritage.", "Oct - Mar", 15000, "https://images.unsplash.com/photo-1603262110263-fb010d6e59d4?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Manali", "Manali", "India", "Mountain", "Picturesque hill station nestled in Himalayas, snow peaks, Solang Valley and Rohtang Pass.", "Sep - Jun", 22000, "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=800&q=80", 4.6, 1),
    ("Kerala Backwaters", "Alleppey", "India", "Beach", "Serene palm-fringed backwaters, luxury houseboats, and Ayurvedic retreats.", "Oct - Mar", 25000, "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Munnar", "Munnar", "India", "Mountain", "Rolling emerald tea plantations, misty mountains, and cool high-altitude climate.", "Sep - May", 16000, "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Leh Ladakh", "Leh", "India", "Adventure", "High-altitude desert, Pangong Lake, ancient Buddhist gompas, and scenic mountain passes.", "May - Sep", 35000, "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Varanasi", "Varanasi", "India", "Spiritual", "Spiritual capital of India along sacred River Ganges with mesmerizing Ganga Aarti.", "Oct - Mar", 12000, "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Agra", "Agra", "India", "Heritage", "Home of the iconic Taj Mahal, Agra Fort, and timeless Mughal architectural masterpieces.", "Oct - Mar", 10000, "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Udaipur", "Udaipur", "India", "Heritage", "The City of Lakes with romantic Lake Pichola, royal palaces, and sunset boat rides.", "Sep - Mar", 24000, "https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Ooty", "Ooty", "India", "Mountain", "Queen of Nilgiri Hill Stations, Nilgiri Mountain Railway, botanical gardens, and pine forests.", "All Year", 14000, "https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=800&q=80", 4.5, 0),
    ("Rishikesh", "Rishikesh", "India", "Adventure", "Yoga capital of the world, white water river rafting, bungee jumping, and serene ghats.", "Sep - May", 12000, "https://images.unsplash.com/photo-1600100397608-f010f4439c06?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Andaman Islands", "Port Blair", "India", "Island", "Turquoise waters, pristine coral reefs, Radhanagar Beach, scuba diving and bioluminescence.", "Oct - May", 40000, "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Shillong", "Shillong", "India", "Mountain", "Scotland of the East, cascading waterfalls, living root bridges, and rolling green pine hills.", "Sep - May", 20000, "https://images.unsplash.com/photo-1598890777032-bde835ba27c2?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Kolkata", "Kolkata", "India", "Urban", "Cultural capital of India, Victoria Memorial, Howrah Bridge, colonial trams and delicious sweets.", "Oct - Mar", 12000, "https://images.unsplash.com/photo-1558431382-27e303142255?auto=format&fit=crop&w=800&q=80", 4.5, 0),
    ("Mumbai", "Mumbai", "India", "Urban", "City of Dreams, Marine Drive sunset, Gateway of India, Bollywood, and iconic street cuisine.", "Nov - Feb", 25000, "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=800&q=80", 4.6, 1),
    ("Bengaluru", "Bengaluru", "India", "Urban", "Garden City & tech hub, lush Cubbon Park, microbreweries, and lively cultural spaces.", "All Year", 18000, "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80", 4.4, 0),
    ("Darjeeling", "Darjeeling", "India", "Mountain", "World-renowned tea estates, sunrise view of Kanchenjunga from Tiger Hill, and toy train.", "Mar - Jun, Sep - Nov", 18000, "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Hampi", "Hampi", "India", "Heritage", "UNESCO World Heritage site with boulder-strewn landscape, ancient Vijayanagara ruins and temples.", "Oct - Feb", 11000, "https://images.unsplash.com/photo-1600100397608-f010f4439c06?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Coorg", "Madikeri", "India", "Mountain", "Coffee plantations, mist-covered valleys, Abbey Falls, and peaceful Kodava culture.", "Oct - Mar", 15000, "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Pondicherry", "Puducherry", "India", "Beach", "French colonial quarters, yellow villas, Promenade Beach, and spiritual Auroville.", "Oct - Mar", 14000, "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Amritsar", "Amritsar", "India", "Spiritual", "Sacred Golden Temple, spiritual community kitchen Langar, and historic Wagah Border ceremony.", "Oct - Mar", 10000, "https://images.unsplash.com/photo-1588096344356-9b49742617f0?auto=format&fit=crop&w=800&q=80", 4.9, 0),
    ("Srinagar", "Srinagar", "India", "Mountain", "Paradise on Earth, Dal Lake shikara rides, Mughal Gardens, and snow-capped peaks.", "Apr - Oct", 30000, "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Jaisalmer", "Jaisalmer", "India", "Heritage", "Golden City in Thar desert, living fort, camel desert safaris, and stargazing camps.", "Oct - Mar", 16000, "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Kaziranga", "Golaghat", "India", "Wildlife", "World heritage wildlife sanctuary, habitat of world's largest population of one-horned rhinos.", "Nov - Apr", 19000, "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Mysore", "Mysuru", "India", "Heritage", "Grand Mysore Palace, royal Dasara festival heritage, silk weaving, and sandalwood crafts.", "Oct - Mar", 11000, "https://images.unsplash.com/photo-1600100397608-f010f4439c06?auto=format&fit=crop&w=800&q=80", 4.5, 0),
    ("Shimla", "Shimla", "India", "Mountain", "Historic summer capital of British India, Mall Road, Ridge, and alpine pine forests.", "Mar - Jun, Dec - Jan", 17000, "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=800&q=80", 4.5, 0),
    ("Gangtok", "Gangtok", "India", "Mountain", "Capital of Sikkim, breathtaking mountain views, Enchey Monastery, and Nathu La Pass.", "Sep - Jun", 21000, "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Ranthambore", "Sawai Madhopur", "India", "Wildlife", "Famous tiger reserve, royal Bengal tiger safaris, and ancient Ranthambore Fort ruins.", "Oct - Apr", 22000, "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Mahabalipuram", "Mamallapuram", "India", "Heritage", "Rock-cut cave temples, monolithic shore temple, and ancient stone-carving traditions.", "Nov - Feb", 12000, "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Gokarna", "Gokarna", "India", "Beach", "Peaceful secluded beaches, Om Beach trekking, Mahabaleshwar Temple, and tranquil vibes.", "Oct - Mar", 11000, "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Kanyakumari", "Kanyakumari", "India", "Spiritual", "Southernmost tip of mainland India, confluence of three oceans, and Vivekananda Rock.", "Oct - Mar", 13000, "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=800&q=80", 4.5, 0),
    ("Nainital", "Nainital", "India", "Mountain", "Scenic lake city surrounded by seven hills, Naini Lake boating, and snow view point.", "Mar - Jun, Sep - Nov", 14000, "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=800&q=80", 4.4, 0),
    ("Hyderabad", "Hyderabad", "India", "Urban", "City of Pearls, majestic Charminar, Golconda Fort, and world-famous Hyderabadi Biryani.", "Oct - Mar", 15000, "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=800&q=80", 4.6, 0),
    ("Khajuraho", "Khajuraho", "India", "Heritage", "Stunning medieval Hindu and Jain temples adorned with intricate sculptures.", "Oct - Mar", 12000, "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Cherrapunji", "Sohra", "India", "Adventure", "Wettest place on earth, Nohkalikai Falls, caves exploration, and double decker root bridges.", "Oct - May", 19000, "https://images.unsplash.com/photo-1598890777032-bde835ba27c2?auto=format&fit=crop&w=800&q=80", 4.7, 0),

    # International Destinations (25)
    ("Paris", "Paris", "France", "Urban", "City of Light, iconic Eiffel Tower, Louvre Museum, Notre-Dame, and Parisian cafes.", "Apr - Oct", 120000, "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Dubai", "Dubai", "UAE", "Urban", "Futuristic metropolis, Burj Khalifa, desert safari adventures, luxury shopping, and marina.", "Nov - Mar", 85000, "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Tokyo", "Tokyo", "Japan", "Urban", "Neon-lit streets of Shinjuku, historic temples of Asakusa, cherry blossoms, and sushi cuisine.", "Mar - May, Sep - Nov", 140000, "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Bali", "Denpasar", "Indonesia", "Island", "Tropical paradise of Ubud rice terraces, Uluwatu cliff temple, surfing, and yoga sanctuaries.", "Apr - Oct", 65000, "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Rome", "Rome", "Italy", "Heritage", "Eternal City, Colosseum, Vatican City, Roman Forum, Trevi Fountain, and authentic pasta.", "Apr - Jun, Sep - Oct", 110000, "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("London", "London", "UK", "Urban", "Historic Thames river, Tower Bridge, Buckingham Palace, West End theaters, and rich museums.", "May - Sep", 130000, "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("New York", "New York", "USA", "Urban", "The Big Apple, Times Square, Central Park, Empire State Building, and Broadway shows.", "Apr - Jun, Sep - Nov", 160000, "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Singapore", "Singapore", "Singapore", "Urban", "Marina Bay Sands, futuristic Gardens by the Bay, Sentosa Island, and world-class street food.", "All Year", 75000, "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=800&q=80", 4.8, 1),
    ("Bangkok", "Bangkok", "Thailand", "Urban", "Vibrant street life, ornate Grand Palace, Wat Arun, floating markets, and nightlife.", "Nov - Feb", 45000, "https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Maldives", "Male", "Maldives", "Island", "Overwater bungalows, crystal lagoon waters, vibrant marine life, and luxury coral atolls.", "Nov - Apr", 115000, "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Zurich", "Zurich", "Switzerland", "Mountain", "Alpine wonderland, Lake Zurich, Swiss chocolates, scenic train journeys, and snowy peaks.", "Jun - Sep, Dec - Mar", 175000, "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Sydney", "Sydney", "Australia", "Urban", "Sydney Opera House, Harbour Bridge, Bondi Beach surf, coastal walks, and wildlife.", "Sep - Nov, Mar - May", 150000, "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Cape Town", "Cape Town", "South Africa", "Adventure", "Table Mountain cableway, Cape of Good Hope, penguin beaches, and scenic winelands.", "Nov - Mar", 120000, "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Cairo", "Cairo", "Egypt", "Heritage", "Great Pyramids of Giza, Sphinx, Nile River cruise, and treasures of King Tutankhamun.", "Oct - Apr", 80000, "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Barcelona", "Barcelona", "Spain", "Urban", "Gaudí architecture, Sagrada Família, Park Güell, Mediterranean beaches, and tapas bars.", "May - Jun, Sep - Oct", 105000, "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Istanbul", "Istanbul", "Turkey", "Heritage", "Where East meets West, Hagia Sophia, Blue Mosque, Grand Bazaar, and Bosphorus Strait.", "Apr - May, Sep - Nov", 70000, "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=80", 4.8, 0),
    ("Amsterdam", "Amsterdam", "Netherlands", "Urban", "Historic canals, Van Gogh Museum, Anne Frank House, windmills, and bicycle culture.", "Apr - May, Sep - Nov", 115000, "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Rio de Janeiro", "Rio de Janeiro", "Brazil", "Beach", "Christ the Redeemer, Copacabana beach, Sugarloaf Mountain, and samba rhythms.", "Dec - Mar", 135000, "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Santorini", "Fira", "Greece", "Island", "Iconic whitewashed cliffside villages, blue-domed churches, and world-famous Aegean sunsets.", "May - Oct", 125000, "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=800&q=80", 4.9, 1),
    ("Kyoto", "Kyoto", "Japan", "Heritage", "Historic capital with thousands of classical Buddhist temples, bamboo groves, and geisha districts.", "Mar - May, Oct - Nov", 130000, "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=800&q=80", 4.9, 0),
    ("Prague", "Prague", "Czech Republic", "Heritage", "City of a Hundred Spires, historic Charles Bridge, Old Town Square astronomical clock.", "May - Sep", 85000, "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Reykjavik", "Reykjavik", "Iceland", "Adventure", "Land of Fire and Ice, Northern Lights, geothermal Blue Lagoon, waterfalls, and glaciers.", "Sep - Mar, Jun - Aug", 185000, "https://images.unsplash.com/photo-1504893524553-b855bce32c67?auto=format&fit=crop&w=800&q=80", 4.9, 0),
    ("Queenstown", "Queenstown", "New Zealand", "Adventure", "Adventure capital of the Southern Hemisphere, Lake Wakatipu, bungee jumping, and fiords.", "Dec - Feb, Jun - Aug", 165000, "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?auto=format&fit=crop&w=800&q=80", 4.9, 0),
    ("Phuket", "Phuket", "Thailand", "Beach", "Tropical Andaman beaches, limestone karst islands, nightlife, and sea kayaking tours.", "Nov - Apr", 50000, "https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?auto=format&fit=crop&w=800&q=80", 4.7, 0),
    ("Vienna", "Vienna", "Austria", "Heritage", "Imperial palaces of Schönbrunn and Hofburg, classical music legacy, and historic cafe culture.", "Apr - Oct", 115000, "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=800&q=80", 4.8, 0)
]

AIRLINES = [
    "IndiGo", "Air India", "Emirates", "Singapore Airlines", "Qatar Airways",
    "Vistara", "Lufthansa", "British Airways", "Etihad Airways", "SpiceJet"
]

HOTEL_ADJECTIVES = ["Grand", "Royal", "The Oberoi", "Taj", "Marriott", "Hyatt Regency", "Radisson Blu", "Heritage", "Serene", "Boutique", "Lakeside", "Sunset", "Emerald", "Azure", "Imperial"]
HOTEL_TYPES = ["Luxury Resort", "Boutique Hotel", "Business Hotel", "Heritage Villa", "Budget Hotel"]
AMENITY_LISTS = [
    "Free High-Speed Wi-Fi, Outdoor Infinity Pool, Luxury Spa, Ocean View, Complimentary Breakfast, 24/7 Room Service",
    "Free Wi-Fi, Mountain View Balcony, Heated Pool, Fireplace, Multi-cuisine Restaurant, Fitness Center",
    "Free Wi-Fi, Executive Lounge, Airport Shuttle, Business Center, Multi-Cuisine Dining, Valet Parking",
    "Free Wi-Fi, Private Beach Access, Ayurvedic Wellness Spa, Scuba Gear Rental, Sunrise Breakfast Deck",
    "Free Wi-Fi, Rooftop Terrace Restaurant, Air Conditioning, Concierge Desk, Heritage Architecture, Tea Lounge"
]


def seed_all_data(force_reset: bool = False):
    """Executes schema initialization and seeds all 8 relational domains."""
    print("=" * 60)
    print("TRAVELNEST: Initializing Relational Database & Seed Data")
    print("=" * 60)

    # 1. Initialize DB Schema
    success, msg = init_db()
    if not success:
        print(f"Error during init_db: {msg}")
        return False
    print(f"Database check passed: {msg}")

    # Check if already seeded and not force reset
    user_count = fetch_one("SELECT COUNT(*) as cnt FROM users")
    if user_count and user_count["cnt"] >= 10 and not force_reset:
        print("Database already contains seeded records. Generating CSV exports to maintain consistency...")
        _export_all_csvs()
        return True

    # 2. Seed Users
    print("Seeding Users...")
    users_to_insert = [
        ("admin@travelnest.com", "Admin@123", "System Administrator", "admin", "+91 98765 43210"),
        ("user@travelnest.com", "User@123", "Aarav Sharma", "customer", "+91 98765 00001"),
        ("priya@travelnest.com", "Priya@123", "Priya Patel", "customer", "+91 98765 00002"),
        ("rohan@travelnest.com", "Rohan@123", "Rohan Verma", "customer", "+91 98765 00003"),
        ("ananya@travelnest.com", "Ananya@123", "Ananya Iyer", "customer", "+91 98765 00004"),
        ("vikram@travelnest.com", "Vikram@123", "Vikram Malhotra", "customer", "+91 98765 00005"),
        ("neha@travelnest.com", "Neha@123", "Neha Gupta", "customer", "+91 98765 00006"),
        ("karan@travelnest.com", "Karan@123", "Karan Singh", "customer", "+91 98765 00007"),
        ("sneha@travelnest.com", "Sneha@123", "Sneha Joshi", "customer", "+91 98765 00008"),
        ("arjun@travelnest.com", "Arjun@123", "Arjun Reddy", "customer", "+91 98765 00009"),
        ("divya@travelnest.com", "Divya@123", "Divya Nair", "customer", "+91 98765 00010"),
        ("rahul@travelnest.com", "Rahul@123", "Rahul Mehta", "customer", "+91 98765 00011"),
        ("pooja@travelnest.com", "Pooja@123", "Pooja Banerjee", "customer", "+91 98765 00012"),
        ("aditya@travelnest.com", "Aditya@123", "Aditya Rao", "customer", "+91 98765 00013"),
        ("riya@travelnest.com", "Riya@123", "Riya Sen", "customer", "+91 98765 00014"),
        ("siddharth@travelnest.com", "Siddharth@123", "Siddharth Roy", "customer", "+91 98765 00015"),
        ("meera@travelnest.com", "Meera@123", "Meera Krishnan", "customer", "+91 98765 00016"),
        ("tanvi@travelnest.com", "Tanvi@123", "Tanvi Deshmukh", "customer", "+91 98765 00017"),
        ("varun@travelnest.com", "Varun@123", "Varun Kapoor", "customer", "+91 98765 00018"),
        ("ishaan@travelnest.com", "Ishaan@123", "Ishaan Bhatia", "customer", "+91 98765 00019")
    ]

    user_id_map = {}
    for email, pwd, name, role, phone in users_to_insert:
        existing = fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
        if not existing:
            salt = generate_salt()
            pwd_hash = hash_password(pwd, salt)
            uid = execute_commit(
                "INSERT INTO users (email, password_hash, salt, full_name, role, phone, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (email, pwd_hash, salt, name, role, phone, datetime.datetime.now() - datetime.timedelta(days=random.randint(30, 200)))
            )
            user_id_map[email] = uid
        else:
            user_id_map[email] = existing["user_id"]

    # 3. Seed Destinations (60 destinations)
    print("Seeding 60 Destinations...")
    dest_id_map = {}
    for name, city, state_country, category, desc, btime, budget, img, rating, feat in DESTINATIONS_DATA:
        existing = fetch_one("SELECT destination_id FROM destinations WHERE name = %s", (name,))
        if not existing:
            did = execute_commit(
                """INSERT INTO destinations (name, city, state_country, category, description, best_time_to_visit, estimated_budget, image_url, rating, is_featured, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, city, state_country, category, desc, btime, budget, img, rating, feat, datetime.datetime.now() - datetime.timedelta(days=180))
            )
            dest_id_map[name] = did
        else:
            dest_id_map[name] = existing["destination_id"]

    dest_ids = list(dest_id_map.values())
    dest_names = list(dest_id_map.keys())

    # 4. Seed Hotels (150 Hotels)
    print("Seeding 150 Hotels & Rooms...")
    hotel_count = fetch_one("SELECT COUNT(*) as cnt FROM hotels")["cnt"]
    hotel_ids = []
    if hotel_count < 150:
        for i in range(150):
            d_name = dest_names[i % len(dest_names)]
            d_id = dest_id_map[d_name]
            adj = random.choice(HOTEL_ADJECTIVES)
            prop_type = random.choice(HOTEL_TYPES)
            h_name = f"{adj} {d_name} {prop_type}"
            base_price = random.choice([2800, 3500, 4800, 6500, 8900, 12500, 16000, 22000, 29000])
            star = random.choice([3, 4, 4, 5, 5])
            amenities = random.choice(AMENITY_LISTS)
            img = random.choice([
                "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=800&q=80"
            ])
            address = f"Plot {random.randint(10, 890)}, Heritage Boulevard, {d_name}"
            hid = execute_commit(
                """INSERT INTO hotels (name, destination_id, city, address, star_rating, property_type, amenities, price_per_night, image_url, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (h_name, d_id, d_name, address, star, prop_type, amenities, base_price, img, datetime.datetime.now() - datetime.timedelta(days=120))
            )
            hotel_ids.append(hid)

            # Insert 2-3 room tiers per hotel
            room_tiers = [
                ("Deluxe Standard Room", 2, base_price, 12),
                ("Executive Suite", 3, round(base_price * 1.5), 6),
                ("Royal Ocean/Panoramic Suite", 4, round(base_price * 2.2), 3)
            ]
            for r_name, cap, r_price, r_avail in room_tiers:
                execute_commit(
                    """INSERT INTO hotel_rooms (hotel_id, room_type, capacity, price_per_night, available_rooms)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (hid, r_name, cap, r_price, r_avail)
                )
    else:
        rows = execute_query("SELECT hotel_id FROM hotels LIMIT 150", fetch="all")
        hotel_ids = [r["hotel_id"] for r in rows]

    # 5. Seed Flights (500 Flights)
    print("Seeding 500 Flights...")
    flight_count = fetch_one("SELECT COUNT(*) as cnt FROM flights")["cnt"]
    hub_cities = ["Delhi", "Mumbai", "Bengaluru", "Goa", "Jaipur", "Dubai", "Singapore", "London", "Paris", "Bangkok", "Tokyo", "Zurich", "Kolkata", "Hyderabad", "Chennai"]
    classes = ["Economy", "Premium Economy", "Business", "First"]

    if flight_count < 500:
        base_date = datetime.datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        for i in range(500):
            airline = random.choice(AIRLINES)
            code_prefix = airline[:2].upper() if len(airline) >= 2 else "TN"
            f_num = f"{code_prefix}-{random.randint(101, 989)}"
            src = random.choice(hub_cities)
            dest = random.choice([c for c in hub_cities if c != src])
            dep_offset_days = random.randint(1, 90)
            dep_hour = random.randint(5, 23)
            dep_min = random.choice([0, 15, 30, 45])
            dep_time = base_date + datetime.timedelta(days=dep_offset_days, hours=dep_hour, minutes=dep_min)

            duration = random.randint(90, 600)  # 1.5 hrs to 10 hrs
            arr_time = dep_time + datetime.timedelta(minutes=duration)
            stops = 0 if duration <= 180 else random.choice([0, 1, 1, 2])
            t_class = random.choice(["Economy", "Economy", "Economy", "Premium Economy", "Business"])

            # Realistic pricing based on class and duration
            base_rate = duration * 25
            class_mult = {"Economy": 1.0, "Premium Economy": 1.6, "Business": 3.2, "First": 5.5}[t_class]
            price = round(base_rate * class_mult) + random.randint(50, 450)

            # Prevent duplicate flight_number
            unique_f_num = f"{f_num}-{i+1}"
            execute_commit(
                """INSERT INTO flights (flight_number, airline, source_city, destination_city, departure_time, arrival_time, duration_minutes, stops, travel_class, price, seats_available, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (unique_f_num, airline, src, dest, dep_time, arr_time, duration, stops, t_class, price, random.randint(15, 120), datetime.datetime.now() - datetime.timedelta(days=30))
            )

    # 6. Seed Travel Packages (100 Packages)
    print("Seeding 100 Travel Packages...")
    pkg_count = fetch_one("SELECT COUNT(*) as cnt FROM travel_packages")["cnt"]
    pkg_ids = []
    package_types = ["Domestic", "International", "Honeymoon", "Adventure", "Family", "Solo"]
    package_themes = [
        "Enchanting Escape", "Royal Heritage Discovery", "Tropical Wilderness Expedition",
        "Grand Highlights Tour", "Romantic Gateway", "Hidden Gems Trail", "Epic Scenic Circuit",
        "Cultural Splendor & Culinary Tour"
    ]

    if pkg_count < 100:
        for i in range(100):
            d_name = dest_names[i % len(dest_names)]
            d_id = dest_id_map[d_name]
            theme = random.choice(package_themes)
            title = f"{theme}: {d_name} Explorer"
            ptype = "International" if d_name in [
                "Paris", "Dubai", "Tokyo", "Bali", "Rome", "London", "New York", "Singapore",
                "Bangkok", "Maldives", "Zurich", "Sydney", "Cape Town", "Cairo", "Barcelona",
                "Istanbul", "Amsterdam", "Rio de Janeiro", "Santorini", "Kyoto", "Prague",
                "Reykjavik", "Queenstown", "Phuket", "Vienna"
            ] else random.choice(["Domestic", "Honeymoon", "Family", "Adventure"])

            days = random.choice([3, 4, 5, 6, 7, 10])
            nights = days - 1
            itinerary = (
                f"Day 1: Arrival in {d_name}, private transfer to 4-star hotel, welcome dinner.\n"
                f"Day 2: Guided morning landmarks tour, cultural museum visit, sunset viewpoint.\n"
                f"Day 3: Outdoor excursion, local gastronomy experience, leisure shopping.\n"
                f"Day {days}: Morning breakfast, souvenir bazaar exploration, airport transfer."
            )
            inclusions = "Handpicked 4-Star Accommodations, Daily Gourmet Breakfast, Dedicated Guide, AC Private Vehicle, Monument Entrances, 24/7 Concierge."
            pkg_price = round(random.choice([18000, 24000, 35000, 52000, 78000, 95000, 135000]) * (days / 4))
            img = random.choice([
                "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=800&q=80"
            ])
            pid = execute_commit(
                """INSERT INTO travel_packages (destination_id, title, package_type, duration_days, duration_nights, itinerary_summary, inclusions, price, max_group_size, image_url, is_featured, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (d_id, title, ptype, days, nights, itinerary, inclusions, pkg_price, random.randint(12, 25), img, 1 if i % 5 == 0 else 0, datetime.datetime.now() - datetime.timedelta(days=90))
            )
            pkg_ids.append(pid)
    else:
        rows = execute_query("SELECT package_id FROM travel_packages LIMIT 100", fetch="all")
        pkg_ids = [r["package_id"] for r in rows]

    # 7. Seed Activities (200 Activities)
    print("Seeding 200 Activities...")
    act_count = fetch_one("SELECT COUNT(*) as cnt FROM activities")["cnt"]
    act_ids = []
    act_categories = ["Water Sports", "Sightseeing", "Trekking", "Cultural", "Culinary", "Safari", "Adventure"]
    activity_templates = [
        ("Sunrise Hot Air Balloon Flight", "Adventure", 3.0, 8500),
        ("Guided Heritage Walking Tour & Tasting", "Cultural", 3.5, 1800),
        ("Sunset Luxury Catamaran Cruise", "Water Sports", 2.5, 4200),
        ("Scuba Diving Discovery & Reef Tour", "Water Sports", 4.0, 5500),
        ("Wild Jungle Jeep Safari & Tracking", "Safari", 4.5, 3800),
        ("High Alpine Peak Trekking Excursion", "Trekking", 6.0, 2900),
        ("Masterclass Cooking Workshop & Market Tour", "Culinary", 3.0, 2400),
        ("Historic Monuments Skip-the-Line Tour", "Sightseeing", 3.5, 1500),
        ("Desert Stargazing & Bedouin Camp Dinner", "Adventure", 5.0, 4800),
        ("River Rafting Rapids Adventure", "Water Sports", 3.0, 2100)
    ]

    if act_count < 200:
        for i in range(200):
            d_name = dest_names[i % len(dest_names)]
            d_id = dest_id_map[d_name]
            tpl_title, tpl_cat, tpl_dur, tpl_price = random.choice(activity_templates)
            title = f"{tpl_title} in {d_name}"
            loc = f"Central {d_name} District"
            img = random.choice([
                "https://images.unsplash.com/photo-1527631746610-bca00a040d60?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=800&q=80"
            ])
            aid = execute_commit(
                """INSERT INTO activities (destination_id, title, category, duration_hours, location, price, image_url, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (d_id, title, tpl_cat, tpl_dur, loc, tpl_price + random.randint(-200, 800), img, datetime.datetime.now() - datetime.timedelta(days=60))
            )
            act_ids.append(aid)
    else:
        rows = execute_query("SELECT activity_id FROM activities LIMIT 200", fetch="all")
        act_ids = [r["activity_id"] for r in rows]

    # 8. Seed Trip Plans (100 Trips)
    print("Seeding 100 Trip Plans...")
    trip_count = fetch_one("SELECT COUNT(*) as cnt FROM trips")["cnt"]
    u_ids = list(user_id_map.values())
    trip_ids = []
    trip_statuses = ["Planning", "Upcoming", "Completed", "Cancelled"]

    if trip_count < 100:
        for i in range(100):
            uid = random.choice(u_ids)
            d_name = random.choice(dest_names)
            did = dest_id_map[d_name]
            status = random.choice(trip_statuses)
            today = datetime.date.today()

            if status == "Completed":
                s_date = today - datetime.timedelta(days=random.randint(20, 180))
            elif status == "Upcoming":
                s_date = today + datetime.timedelta(days=random.randint(5, 60))
            else:
                s_date = today + datetime.timedelta(days=random.randint(15, 90))
            e_date = s_date + datetime.timedelta(days=random.randint(3, 10))

            title = f"{status} Vacation to {d_name}"
            budget = random.choice([30000, 45000, 60000, 85000, 120000, 180000])
            notes = f"Trip planned for {d_name}. Must explore historical quarters, enjoy local delicacies, and take photography walks."

            tid = execute_commit(
                """INSERT INTO trips (user_id, title, destination_id, start_date, end_date, budget, notes, status, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (uid, title, did, s_date, e_date, budget, notes, status, datetime.datetime.now() - datetime.timedelta(days=random.randint(10, 100)))
            )
            trip_ids.append(tid)

            # Insert trip_destinations link
            execute_commit(
                """INSERT INTO trip_destinations (trip_id, destination_id, visit_order, stay_days)
                   VALUES (%s, %s, %s, %s)""",
                (tid, did, 1, (e_date - s_date).days)
            )
    else:
        rows = execute_query("SELECT trip_id FROM trips LIMIT 100", fetch="all")
        trip_ids = [r["trip_id"] for r in rows]

    # 9. Seed Bookings (300 Bookings)
    print("Seeding 300 Bookings across all categories...")
    booking_count = fetch_one("SELECT COUNT(*) as cnt FROM bookings")["cnt"]
    booking_types = ["Flight", "Hotel", "Package", "Activity"]
    b_statuses = ["Confirmed", "Confirmed", "Completed", "Completed", "Pending", "Cancelled"]

    if booking_count < 300:
        flight_rows = execute_query("SELECT flight_id, airline, flight_number, source_city, destination_city, price FROM flights LIMIT 100", fetch="all")
        hotel_rows = execute_query("SELECT hotel_id, name, price_per_night FROM hotels LIMIT 100", fetch="all")
        pkg_rows = execute_query("SELECT package_id, title, price FROM travel_packages LIMIT 50", fetch="all")
        act_rows = execute_query("SELECT activity_id, title, price FROM activities LIMIT 50", fetch="all")

        today = datetime.date.today()
        for i in range(300):
            b_type = random.choice(booking_types)
            uid = random.choice(u_ids)
            tid = random.choice(trip_ids) if random.random() > 0.4 else None
            status = random.choice(b_statuses)
            guests = random.randint(1, 4)

            # Realistic dates
            if status == "Completed":
                b_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(30, 180))
                start_date = b_date.date() + datetime.timedelta(days=random.randint(2, 10))
            elif status == "Confirmed":
                b_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 45))
                start_date = today + datetime.timedelta(days=random.randint(5, 75))
            else:
                b_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 20))
                start_date = today + datetime.timedelta(days=random.randint(10, 60))

            end_date = start_date + datetime.timedelta(days=random.randint(2, 7))
            cancel_reason = "Schedule conflict due to professional commitments." if status == "Cancelled" else None

            if b_type == "Flight" and flight_rows:
                fl = random.choice(flight_rows)
                item_id = fl["flight_id"]
                item_title = f"{fl['airline']} {fl['flight_number']} ({fl['source_city']} → {fl['destination_city']})"
                unit_price = fl["price"]
                total = unit_price * guests
            elif b_type == "Hotel" and hotel_rows:
                ht = random.choice(hotel_rows)
                item_id = ht["hotel_id"]
                item_title = f"{ht['name']}"
                nights = (end_date - start_date).days or 1
                unit_price = ht["price_per_night"]
                total = unit_price * nights * max(1, guests // 2)
            elif b_type == "Package" and pkg_rows:
                pk = random.choice(pkg_rows)
                item_id = pk["package_id"]
                item_title = f"{pk['title']}"
                unit_price = pk["price"]
                total = unit_price * guests
            elif act_rows:
                ac = random.choice(act_rows)
                item_id = ac["activity_id"]
                item_title = f"{ac['title']}"
                unit_price = ac["price"]
                total = unit_price * guests
            else:
                continue

            ref = generate_booking_reference(b_type)
            execute_commit(
                """INSERT INTO bookings (booking_reference, user_id, trip_id, booking_type, item_id, item_title, booking_date, travel_start_date, travel_end_date, num_guests, unit_price, total_price, status, cancellation_reason, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (ref, uid, tid, b_type, item_id, item_title, b_date, start_date, end_date, guests, unit_price, total, status, cancel_reason, b_date)
            )

    # 10. Seed Reviews (150 Reviews)
    print("Seeding 150 User Reviews...")
    rev_count = fetch_one("SELECT COUNT(*) as cnt FROM reviews")["cnt"]
    review_templates = [
        (5, "Absolutely breathtaking experience!", "Everything was seamless from start to finish. The views were unbelievable and hospitality was top-notch."),
        (5, "Unforgettable trip, highly recommended!", "TravelNest made the entire booking smooth. Our accommodations exceeded expectations."),
        (4, "Wonderful vacation with great memories", "Very good experience overall. Great guided tour and delightful local delicacies. Will visit again."),
        (4, "Pleasant stay and smooth logistics", "Clean amenities, friendly staff, and great proximity to major attractions."),
        (3, "Decent trip, could be slightly improved", "The location was scenic, though peak season crowds caused some delays. Still enjoyed the experience.")
    ]

    if rev_count < 150:
        inserted_revs = 0
        attempts = 0
        while inserted_revs < 150 and attempts < 600:
            attempts += 1
            uid = random.choice(u_ids)
            target_type = random.choice(["destination", "hotel"])
            target_id = random.choice(dest_ids) if target_type == "destination" else random.choice(hotel_ids)

            # Check if this user already reviewed this target
            exists = fetch_one(
                "SELECT review_id FROM reviews WHERE user_id = %s AND target_type = %s AND target_id = %s",
                (uid, target_type, target_id)
            )
            if not exists:
                rating, title, comment = random.choice(review_templates)
                execute_commit(
                    """INSERT INTO reviews (user_id, target_type, target_id, rating, title, comment, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (uid, target_type, target_id, rating, title, comment, datetime.datetime.now() - datetime.timedelta(days=random.randint(5, 120)))
                )
                inserted_revs += 1

    # 11. Generate CSV Exports
    print("Exporting all tables to data/*.csv...")
    _export_all_csvs()

    print("=" * 60)
    print("TRAVELNEST: Seed dataset generation completed successfully!")
    print("=" * 60)
    return True


def _export_all_csvs():
    """Reads all relational tables and writes fresh CSV files to data/ directory."""
    table_files = {
        "destinations": "destinations.csv",
        "flights": "flights.csv",
        "hotels": "hotels.csv",
        "travel_packages": "packages.csv",
        "activities": "activities.csv",
        "bookings": "bookings.csv",
        "reviews": "reviews.csv",
        "trips": "trips.csv"
    }
    for table, filename in table_files.items():
        try:
            records = execute_query(f"SELECT * FROM {table}", fetch="all")
            if records:
                df = pd.DataFrame(records)
                out_path = DATA_DIR / filename
                df.to_csv(out_path, index=False)
                print(f"  [CSV] Exported {len(df)} records -> {out_path.name}")
        except Exception as e:
            print(f"  [CSV] Warning: Failed to export {table}: {e}")


if __name__ == "__main__":
    force = "--reset" in sys.argv or "--force" in sys.argv
    seed_all_data(force_reset=force)
