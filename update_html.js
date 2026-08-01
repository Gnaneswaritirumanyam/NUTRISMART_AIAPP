const fs = require('fs');
const path = require('path');

const frontendDir = path.join(__dirname, 'frontend');

// All standard pages in this app
const pages = [
  'dashboard', 'login', 'cuisine', 'reviews', 'profile', 'budget',
  'ai', 'scan', 'intro', 'items', 'loss', 'health', 'gain', 'fitness',
  'meal', 'recipe', 'budgetbased', 'about', 'index'
];

function processFile(filePath) {
    let content = fs.readFileSync(filePath, 'utf-8');

    // 1. Replace fetch
    content = content.replace(/\bfetch\s*\(/g, 'apiFetch(');

    // 2. Replace /static/ with ./
    content = content.replace(/"\/static\//g, '"./');
    content = content.replace(/'\/static\//g, "'./");

    // 3. Replace page navigation hrefs
    pages.forEach(page => {
        // e.g. href="/login" -> href="./login.html"
        // Need to be careful with index (which is / or /index)
        const regex1 = new RegExp(`href=["']/` + page + `["']`, 'g');
        content = content.replace(regex1, `href="./${page}.html"`);

        const regex2 = new RegExp(`window\\.location\\.href\\s*=\\s*["']/` + page + `["']`, 'g');
        content = content.replace(regex2, `window.location.href = "./${page}.html"`);
    });

    // Replace root / with ./index.html
    content = content.replace(/href=["']\/["']/g, 'href="./index.html"');
    content = content.replace(/window\.location\.href\s*=\s*["']\/["']/g, 'window.location.href = "./index.html"');
    
    // Fix any double replacements or issues if necessary
    
    // Inject api_config.js if not present
    if (!content.includes('api_config.js')) {
        const scriptTag = '<script src="./js/api_config.js"></script>\n';
        // Insert before the first script tag, or before </body>
        const firstScriptIndex = content.indexOf('<script');
        if (firstScriptIndex !== -1) {
            content = content.slice(0, firstScriptIndex) + scriptTag + content.slice(firstScriptIndex);
        } else {
            const bodyEndIndex = content.indexOf('</body>');
            if (bodyEndIndex !== -1) {
                content = content.slice(0, bodyEndIndex) + scriptTag + content.slice(bodyEndIndex);
            } else {
                content += '\n' + scriptTag;
            }
        }
    }

    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`Updated ${filePath}`);
}

const files = fs.readdirSync(frontendDir).filter(f => f.endsWith('.html'));
files.forEach(file => {
    processFile(path.join(frontendDir, file));
});

console.log("Done updating HTML files.");
