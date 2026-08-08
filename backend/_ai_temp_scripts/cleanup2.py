from main import userdata_col, recipe_info_map

valid_names = {k.strip().lower() for k in recipe_info_map.keys()}

users = userdata_col.find({"favorites": {"$exists": True}})
removed_count = 0

for u in users:
    email = u.get("email")
    favs = u.get("favorites", [])
    for fav in favs:
        title = fav.get("title", "")
        if title.strip().lower() not in valid_names:
            print(f"Removing invalid recipe title: {title}")
            userdata_col.update_one(
                {"email": email},
                {"$pull": {"favorites": {"title": title}}}
            )
            removed_count += 1

print(f"Total invalid favorites removed: {removed_count}")
