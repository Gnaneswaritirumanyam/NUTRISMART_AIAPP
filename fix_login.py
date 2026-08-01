import re

filename = r'c:\Users\tirum\OneDrive\Desktop\myapp\frontend\login.html'
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

# The file is currently missing the form submission try-catch properly.
# Let's find: `if (!password) {` ... `if (playPromise !== undefined) {` and replace everything between.

start_marker = "if (!password) {"
end_marker = "if (playPromise !== undefined) {"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    correct_block = """if (!password) {
    document.getElementById('passwordError').innerText = 'Please enter your password';
    hasError = true;
  }
  if (hasError) return;

  try {
    const response = await apiFetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include'
    });
    const data = await response.json();
    if (response.ok) {
      localStorage.setItem("user_name", data.name);
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
      }
      
      const successVideo = document.getElementById('successVideo');
      const form = document.querySelector('.glass-form');
      if (form) form.style.display = 'none';

      // Show video
      successVideo.style.display = 'block';
      successVideo.currentTime = 0;

      // Try playing with sound
      successVideo.muted = false;
      const playPromise = successVideo.play();

      """
    
    content = content[:start_idx] + correct_block + content[end_idx:]
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed login.html")
else:
    print("Markers not found")
