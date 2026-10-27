-- ========================================================
-- TRAVELNEST — Relational Database Schema
-- DBMS: MySQL 8.0+
-- Database: travelnest_db
-- ========================================================

CREATE DATABASE IF NOT EXISTS travelnest_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE travelnest_db;

-- --------------------------------------------------------
-- 1. Table: users
-- Stores customer and administrator profiles with salted password hashes
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
    account_status ENUM('active', 'pending', 'suspended', 'rejected') NOT NULL DEFAULT 'active',
    phone VARCHAR(20) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (account_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 1b. Table: admin_enrollment_requests
-- Stores privileged administrator enrollment requests awaiting authorization
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_enrollment_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    reviewed_by INT DEFAULT NULL,
    reviewed_at DATETIME DEFAULT NULL,
    rejection_reason VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_aer_user (user_id),
    INDEX idx_aer_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 2. Table: destinations
-- Indian and International travel destinations
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS destinations (
    destination_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state_country VARCHAR(100) NOT NULL,
    category ENUM('Beach', 'Mountain', 'Heritage', 'Urban', 'Wildlife', 'Adventure', 'Island', 'Spiritual') NOT NULL DEFAULT 'Heritage',
    description TEXT NOT NULL,
    best_time_to_visit VARCHAR(120) DEFAULT 'Oct - Mar',
    estimated_budget DECIMAL(10, 2) NOT NULL DEFAULT 15000.00,
    image_url VARCHAR(500) DEFAULT NULL,
    rating DECIMAL(3, 2) NOT NULL DEFAULT 4.50,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dest_city (city),
    INDEX idx_dest_country (state_country),
    INDEX idx_dest_category (category),
    INDEX idx_dest_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 3. Table: flights
-- Airline routes, schedules, classes, and pricing (Demonstration Dataset)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL UNIQUE,
    airline VARCHAR(100) NOT NULL,
    source_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    duration_minutes INT NOT NULL,
    stops INT NOT NULL DEFAULT 0,
    travel_class ENUM('Economy', 'Premium Economy', 'Business', 'First') NOT NULL DEFAULT 'Economy',
    price DECIMAL(10, 2) NOT NULL,
    seats_available INT NOT NULL DEFAULT 60,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_flight_route (source_city, destination_city),
    INDEX idx_flight_dep (departure_time),
    INDEX idx_flight_airline (airline),
    INDEX idx_flight_class (travel_class),
    INDEX idx_flight_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 4. Table: hotels
-- Lodging accommodations across destinations
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    destination_id INT NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    star_rating INT NOT NULL DEFAULT 4,
    property_type ENUM('Luxury Resort', 'Boutique Hotel', 'Business Hotel', 'Heritage Villa', 'Budget Hotel') NOT NULL DEFAULT 'Boutique Hotel',
    amenities TEXT NOT NULL,
    price_per_night DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE,
    INDEX idx_hotel_dest (destination_id),
    INDEX idx_hotel_city (city),
    INDEX idx_hotel_rating (star_rating),
    INDEX idx_hotel_price (price_per_night)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. Table: hotel_rooms
-- Specific room inventories per hotel
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS hotel_rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    room_type VARCHAR(80) NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    price_per_night DECIMAL(10, 2) NOT NULL,
    available_rooms INT NOT NULL DEFAULT 10,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    INDEX idx_room_hotel (hotel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 6. Table: travel_packages
-- Curated domestic and international vacation packages
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_packages (
    package_id INT AUTO_INCREMENT PRIMARY KEY,
    destination_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    package_type ENUM('Domestic', 'International', 'Honeymoon', 'Adventure', 'Family', 'Solo') NOT NULL DEFAULT 'Domestic',
    duration_days INT NOT NULL DEFAULT 4,
    duration_nights INT NOT NULL DEFAULT 3,
    itinerary_summary TEXT NOT NULL,
    inclusions TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    max_group_size INT NOT NULL DEFAULT 20,
    image_url VARCHAR(500) DEFAULT NULL,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE,
    INDEX idx_pkg_dest (destination_id),
    INDEX idx_pkg_type (package_type),
    INDEX idx_pkg_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 7. Table: activities
-- Excursions, tours, adventure sports and cultural experiences
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    destination_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    category ENUM('Water Sports', 'Sightseeing', 'Trekking', 'Cultural', 'Culinary', 'Safari', 'Adventure') NOT NULL DEFAULT 'Sightseeing',
    duration_hours DECIMAL(4, 1) NOT NULL DEFAULT 3.0,
    location VARCHAR(150) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE,
    INDEX idx_act_dest (destination_id),
    INDEX idx_act_category (category),
    INDEX idx_act_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 8. Table: trips
-- User customized itinerary planning and budget tracking
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips (
    trip_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    destination_id INT DEFAULT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(10, 2) NOT NULL DEFAULT 50000.00,
    notes TEXT DEFAULT NULL,
    status ENUM('Planning', 'Upcoming', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Planning',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE SET NULL,
    INDEX idx_trip_user (user_id),
    INDEX idx_trip_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 9. Table: trip_destinations
-- Multiple destinations linked to a multi-city trip plan
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS trip_destinations (
    trip_dest_id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,
    destination_id INT NOT NULL,
    visit_order INT NOT NULL DEFAULT 1,
    stay_days INT NOT NULL DEFAULT 2,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE,
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id) ON DELETE CASCADE,
    INDEX idx_td_trip (trip_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 10. Table: bookings
-- Confirmed and historical customer transactions across modules
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_reference VARCHAR(30) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    trip_id INT DEFAULT NULL,
    booking_type ENUM('Flight', 'Hotel', 'Package', 'Activity') NOT NULL,
    item_id INT NOT NULL,
    item_title VARCHAR(200) NOT NULL,
    booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    travel_start_date DATE NOT NULL,
    travel_end_date DATE NOT NULL,
    num_guests INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status ENUM('Confirmed', 'Pending', 'Cancelled', 'Completed') NOT NULL DEFAULT 'Confirmed',
    cancellation_reason TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE SET NULL,
    INDEX idx_bk_user (user_id),
    INDEX idx_bk_type (booking_type),
    INDEX idx_bk_status (status),
    INDEX idx_bk_date (booking_date),
    INDEX idx_bk_ref (booking_reference)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 11. Table: reviews
-- Customer feedback and ratings for destinations or hotels
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    target_type ENUM('destination', 'hotel') NOT NULL,
    target_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(150) NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_review (user_id, target_type, target_id),
    INDEX idx_rev_target (target_type, target_id),
    INDEX idx_rev_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
