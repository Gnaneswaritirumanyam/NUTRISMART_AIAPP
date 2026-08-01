import os
import re

LOGIN_FILE = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend\login.html"
SIGNUP_FILE = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend\index.html"

# Google Client ID
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID" # Will be replaced by .env dynamically if possible, or placeholder

def update_login():
    with open(LOGIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Add Google Script
    if "https://accounts.google.com/gsi/client" not in content:
        content = content.replace("</head>", '  <script src="https://accounts.google.com/gsi/client" async defer></script>\n</head>')

    # Add Google Button
    google_btn_html = f"""
    <!-- Google Auth -->
    <div id="g_id_onload"
         data-client_id="{GOOGLE_CLIENT_ID}"
         data-context="signin"
         data-ux_mode="popup"
         data-callback="handleGoogleLogin"
         data-auto_prompt="false">
    </div>
    <div class="g_id_signin"
         data-type="standard"
         data-shape="rectangular"
         data-theme="outline"
         data-text="continue_with"
         data-size="large"
         data-logo_alignment="left"
         style="display: flex; justify-content: center; margin-bottom: 15px;">
    </div>
    <div style="display: flex; align-items: center; text-align: center; margin-bottom: 15px;">
      <hr style="flex: 1; border-top: 1px solid #ccc;">
      <span style="padding: 0 10px; color: #666; font-size: 14px;">OR</span>
      <hr style="flex: 1; border-top: 1px solid #ccc;">
    </div>
"""
    if "g_id_onload" not in content:
        content = content.replace('<form id="loginForm" novalidate>', '<form id="loginForm" novalidate>\n' + google_btn_html)

    # Add Google Callback JS
    google_js = """
async function handleGoogleLogin(response) {
  try {
    const res = await apiFetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("user_name", data.name);
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
      }
      window.location.href = "./intro.html";
    } else {
      alert(data.detail || 'Google Login failed');
    }
  } catch (err) {
    console.error("Google Login error:", err);
    alert('Server error. Try again later.');
  }
}
"""
    if "handleGoogleLogin" not in content:
        content = content.replace("</script>\n</body>", google_js + "\n</script>\n</body>")

    # Update API endpoint for forgot-password
    content = content.replace("await apiFetch('/forgot-password'", "await apiFetch('/api/auth/forgot-password'")

    with open(LOGIN_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated login.html")

def update_signup():
    with open(SIGNUP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Add Google Script
    if "https://accounts.google.com/gsi/client" not in content:
        content = content.replace("</head>", '  <script src="https://accounts.google.com/gsi/client" async defer></script>\n</head>')

    # Add Google Button & OTP HTML
    google_btn_html = f"""
    <!-- Google Auth -->
    <div id="g_id_onload"
         data-client_id="{GOOGLE_CLIENT_ID}"
         data-context="signup"
         data-ux_mode="popup"
         data-callback="handleGoogleLogin"
         data-auto_prompt="false">
    </div>
    <div class="g_id_signin"
         data-type="standard"
         data-shape="rectangular"
         data-theme="outline"
         data-text="continue_with"
         data-size="large"
         data-logo_alignment="left"
         style="display: flex; justify-content: center; margin-bottom: 15px;">
    </div>
    <div style="display: flex; align-items: center; text-align: center; margin-bottom: 15px;">
      <hr style="flex: 1; border-top: 1px solid #ccc;">
      <span style="padding: 0 10px; color: #666; font-size: 14px;">OR</span>
      <hr style="flex: 1; border-top: 1px solid #ccc;">
    </div>
"""
    if "g_id_onload" not in content:
        content = content.replace('<form id="signupForm" novalidate>', '<form id="signupForm" novalidate>\n' + google_btn_html)

    otp_html = """
    <form id="otpForm" style="display: none;" novalidate>
      <div class="mb-3">
        <p>A verification code has been sent to your email.</p>
        <input type="text" id="otpCode" class="form-control" placeholder="6-digit OTP" required maxlength="6">
        <div class="text-danger" id="otpError"></div>
      </div>
      <button type="submit" id="verifyOtpBtn" class="btn btn-primary w-100 mb-2">Verify OTP</button>
      <button type="button" id="resendOtpBtn" class="btn btn-secondary w-100">Resend OTP <span id="resendTimer"></span></button>
    </form>
"""
    if "otpForm" not in content:
        content = content.replace('</form>\n  </div>', '</form>\n' + otp_html + '  </div>')

    # Update JS logic
    js_update = """
async function handleGoogleLogin(response) {
  try {
    const res = await apiFetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("user_name", data.name);
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
      }
      window.location.href = "./intro.html";
    } else {
      alert(data.detail || 'Google Login failed');
    }
  } catch (err) {
    console.error("Google Login error:", err);
    alert('Server error. Try again later.');
  }
}

let userEmail = "";

document.getElementById('signupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Clear previous errors
  ['nameError','emailError','passwordError','confirmPasswordError','recaptchaError'].forEach(id => {
    document.getElementById(id).innerText = '';
  });

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value.trim();
  const confirmPassword = document.getElementById('confirmPassword').value.trim();
  const recaptcha = grecaptcha.getResponse();

  let hasError = false;

  if (!name) { document.getElementById('nameError').innerText = 'Please enter your name'; hasError = true; }
  if (!emailRegex.test(email)) { document.getElementById('emailError').innerText = 'Please enter a valid Gmail'; hasError = true; }
  if (!passwordRegex.test(password)) { document.getElementById('passwordError').innerText = 'Password must include uppercase, lowercase, number, symbol & 8+ chars'; hasError = true; }
  if (password !== confirmPassword) { document.getElementById('confirmPasswordError').innerText = 'Passwords do not match'; hasError = true; }
  if (!recaptcha) { document.getElementById('recaptchaError').innerText = 'Please complete the reCAPTCHA'; hasError = true; }

  if (hasError) return;

  const btn = e.target.querySelector('button[type="submit"]');
  btn.disabled = true;

  try {
    const response = await apiFetch("/api/auth/signup/request-otp", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, confirmPassword, recaptchaToken: recaptcha })
    });

    const data = await response.json();
    if (response.ok) {
      userEmail = email;
      document.getElementById('signupForm').style.display = 'none';
      document.getElementById('otpForm').style.display = 'block';
      startResendCooldown(60);
    } else {
      alert(data.detail || 'Signup failed');
    }
  } catch (err) {
    alert('Server error. Try again later.');
    console.error(err);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('otpForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  document.getElementById('otpError').innerText = '';
  const otp = document.getElementById('otpCode').value.trim();
  if(!otp) {
      document.getElementById('otpError').innerText = 'Please enter OTP';
      return;
  }
  
  const btn = document.getElementById('verifyOtpBtn');
  btn.disabled = true;
  try {
      const response = await apiFetch("/api/auth/signup/verify-otp", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: userEmail, otp })
      });
      const data = await response.json();
      if (response.ok) {
          localStorage.setItem("user_name", data.name);
          if (data.access_token) {
              localStorage.setItem("access_token", data.access_token);
          }
          alert('Signup successful!');
          window.location.href = "./intro.html";
      } else {
          document.getElementById('otpError').innerText = data.detail || 'Invalid OTP';
      }
  } catch (err) {
      alert('Server error.');
  } finally {
      btn.disabled = false;
  }
});

let cooldownTimer;
function startResendCooldown(seconds) {
    const btn = document.getElementById('resendOtpBtn');
    const timerSpan = document.getElementById('resendTimer');
    btn.disabled = true;
    let time = seconds;
    
    clearInterval(cooldownTimer);
    cooldownTimer = setInterval(() => {
        time--;
        if(time <= 0) {
            clearInterval(cooldownTimer);
            timerSpan.innerText = '';
            btn.disabled = false;
        } else {
            timerSpan.innerText = `(${time}s)`;
        }
    }, 1000);
}

document.getElementById('resendOtpBtn').addEventListener('click', async () => {
    const btn = document.getElementById('resendOtpBtn');
    btn.disabled = true;
    try {
        const response = await apiFetch("/api/auth/signup/resend-otp", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: userEmail })
        });
        const data = await response.json();
        if(response.ok) {
            alert('A new OTP has been sent.');
            startResendCooldown(60);
        } else {
            alert(data.detail || 'Failed to resend OTP');
            btn.disabled = false;
        }
    } catch(err) {
        alert('Server error');
        btn.disabled = false;
    }
});
"""

    # Replace the old signup form submit handler
    # Looking for: document.getElementById('signupForm').addEventListener('submit' ... up to the end of the script tag
    import re
    content = re.sub(r"document\.getElementById\('signupForm'\)\.addEventListener\('submit', async \(e\) => \{.*?(?=<!-- For JS -->|</script>)", js_update, content, flags=re.DOTALL)
    
    with open(SIGNUP_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index.html")

if __name__ == "__main__":
    update_login()
    update_signup()
