import sys

content = open('frontend/items.html', 'r', encoding='utf-8').read()

to_replace = """    img.onload = () => {
    console.error("Logout failed:", err);
    alert("Error logging out. Try again.");
  }"""

replacement = """    img.onload = () => {
      const div = document.createElement("div");
      div.className = "recipe-card";
      div.innerHTML = `
        <img src="${r.image}" alt="${cleanName}">
        <h5>${capitalizeWords(cleanName)}</h5>
      `;
      div.addEventListener("click", () => {
        window.location.href = `./recipe.html?cuisine=${encodeURIComponent(cuisine)}&name=${encodeURIComponent(cleanName)}`;
      });
      recipeGrid.appendChild(div);
    };

    img.onerror = () => {
      console.warn(`Skipping recipe "${cleanName}" because image not found: ${r.image}`);
    };
  });
}

// ===== Helper functions =====
function stringSimilarity(a, b) {
  const longer = a.length > b.length ? a : b;
  const shorter = a.length > b.length ? b : a;
  const longerLength = longer.length;
  if (longerLength === 0) return 1.0;
  const editDistance = levenshteinDistance(longer, shorter);
  return (longerLength - editDistance) / parseFloat(longerLength);
}

function levenshteinDistance(s1, s2) {
  const track = Array(s2.length + 1).fill().map(() => []);
  for (let i = 0; i <= s2.length; i++) track[i][0] = i;
  for (let j = 0; j <= s1.length; j++) track[0][j] = j;
  for (let i = 1; i <= s2.length; i++) {
    for (let j = 1; j <= s1.length; j++) {
      track[i][j] = Math.min(
        track[i - 1][j] + 1,
        track[i][j - 1] + 1,
        track[i - 1][j - 1] + (s2[i - 1] === s1[j - 1] ? 0 : 1)
      );
    }
  }
  return track[s2.length][s1.length];
}

// Search functionality
recipeSearch.addEventListener("input", () => {
  const filter = recipeSearch.value.toLowerCase();
  const filtered = recipes.filter(r => r.name.toLowerCase().includes(filter));
  renderRecipes(filtered);
});

// Back arrow
document.getElementById("backArrow").addEventListener("click", () => {
  window.location.href = "./cuisine.html"; // redirect to cuisine page
});

// ===== LOGOUT =====
const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await apiFetch("/api/logout", { method:"POST", credentials:"include" });
      localStorage.removeItem("user_name");
      window.location.href = "./login.html";
    } catch(err) {
      console.error("Logout failed:", err);
      alert("Error logging out. Try again.");
    }
  });
}"""

if to_replace in content:
    content = content.replace(to_replace, replacement)
    with open('frontend/items.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed items.html.")
else:
    print("Could not find the block in items.html")
