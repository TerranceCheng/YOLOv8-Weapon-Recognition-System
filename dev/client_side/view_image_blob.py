import sqlite3
from PIL import Image
import io

# Connect to SQLite database
conn = sqlite3.connect(r"C:\Users\yongt\Desktop\FYP Project\YOLOv8 Weapon Recognition System\dev\db.sqlite3")
cursor = conn.cursor()

# Query to retrieve the image BLOB
cursor.execute("SELECT image_data FROM detection_log WHERE id = ?", (94,))
image_blob = cursor.fetchone()[0]

# Convert the BLOB to an image
image = Image.open(io.BytesIO(image_blob))

# Show the image
image.show()

# Optionally, save the image to a file
image.save("output_image.jpg")

# Close the connection
conn.close()
