import os

path = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend\nutri.html"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove everything from <script> at the bottom to the end, except body closing
script_start = content.find("<script>\n\n\n// ======================================================\n// WEEKLY CALORIE CHART")
if script_start != -1:
    content = content[:script_start] + """
<script src="./js/plan-manager.js"></script>
<script src="./js/notification-manager.js"></script>
<script src="./js/feedback-manager.js"></script>
<script src="./js/analytics-manager.js"></script>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("nutri.html patched successfully.")
else:
    print("Could not find the script block in nutri.html")
