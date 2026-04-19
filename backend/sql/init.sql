CREATE TABLE IF NOT EXISTS dishes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL CHECK (price >= 0),
    description VARCHAR(1000),
    calories TEXT,
    image_url TEXT,
    video_url TEXT,
    subcategory_id INTEGER
);
