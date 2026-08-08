from main import userdata_col
import urllib.parse

bad_title = urllib.parse.unquote('%E0%B4%86%E0%B5%BB%E0%B4%A1%E0%B4%AE%E0%B4%BE%E0%B5%BB%20%E0%B4%B8%E0%B5%8D%E0%B4%B1%E0%B5%8D%E0%B4%B1%E0%B5%88%E0%B5%BD%20%E0%B4%86%E0%B4%B5%E0%B4%BF%E0%B4%AF%E0%B4%BF%E0%B5%BD%20%E0%B4%B5%E0%B5%87%E0%B4%B5%E0%B4%BF%E0%B4%9A%E0%B5%8D%E0%B4%9A%20%E0%B4%B5%E0%B5%86%E0%B4%B3%E0%B5%81%E0%B4%A4%E0%B5%8D%E0%B4%A4%E0%B5%81%E0%B4%B3%E0%B5%8D%E0%B4%B3%E0%B4%BF%20%E0%B4%9A%E0%B5%86%E0%B4%AE%E0%B5%8D%E0%B4%AE%E0%B5%80%E0%B5%BB%20%E0%B4%AA%E0%B4%BE%E0%B4%9A%E0%B4%95%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B5%81%E0%B4%B1%E0%B4%BF%E0%B4%AA%E0%B5%8D%E0%B4%AA%E0%B5%8D')

# Pull the specific bad title
result = userdata_col.update_many(
    {},
    {"$pull": {"favorites": {"title": bad_title}}}
)
print(f"Modified {result.modified_count} users to remove bad_title")

# Clean up any other non-ascii titles just in case
users = userdata_col.find({"favorites": {"$exists": True}})
count = 0
for u in users:
    email = u.get("email")
    favs = u.get("favorites", [])
    bad_favs = [f for f in favs if not f.get("title", "").isascii()]
    if bad_favs:
        for bf in bad_favs:
            userdata_col.update_one({"email": email}, {"$pull": {"favorites": {"title": bf["title"]}}})
            count += 1

print(f"Removed {count} other non-ascii favorites")
