import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class DB_Map():
    def __init__(self, database):
        self.database = database

    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_grapf(self, path, cities):
        """
        path: путь для сохранения PNG
        cities: список названий городов (например, ['Moscow', 'London'])
        """
        # Получаем координаты всех городов
        coords = []
        for city_name in cities:
            c = self.get_coordinates(city_name)
            if c:
                coords.append((city_name, c[0], c[1]))  # (name, lat, lng)

        if not coords:
            return None

        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=False, alpha=0.3)

        lats, lngs = [], []
        for name, lat, lng in coords:
            ax.plot(lng, lat, 'ro', markersize=8, transform=ccrs.PlateCarree())
            plt.text(lng + 1, lat + 1, name, transform=ccrs.PlateCarree(),
                     fontsize=9, fontweight='bold')
            lats.append(lat)
            lngs.append(lng)

        # Масштабирование
        if len(coords) == 1:
            lat, lng = lats[0], lngs[0]
            ax.set_extent([lng - 15, lng + 15, lat - 10, lat + 10], crs=ccrs.PlateCarree())
        else:
            # Подгоняем границы под все города
            min_lat, max_lat = min(lats) - 5, max(lats) + 5
            min_lng, max_lng = min(lngs) - 5, max(lngs) + 5
            # Если разброс большой — показываем мир
            if (max_lat - min_lat) > 90 or (max_lng - min_lng) > 180:
                ax.set_global()
            else:
                ax.set_extent([min_lng, max_lng, min_lat, max_lat], crs=ccrs.PlateCarree())

        plt.title("Города на карте")
        plt.savefig(path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        return path

    def draw_distance(self, city1, city2):
        pass


if __name__ == "__main__":
    m = DB_Map(DATABASE)
    m.create_user_table()