const fs = require('fs');

const content = fs.readFileSync('tests/login-tests.js', 'utf8');

// Find the last test block and replace it
const oldTest = content.substring(content.lastIndexOf('    // ') + 4);

const newEnd = `    // TEST 7: DOM contains expected application content
    it('should contain expected app content on login page', async function () {
        await driver.get(APP_URL);
        const pageSource = await driver.getPageSource();

        // Login page uses Bootstrap + glass-form CSS; title is "Login"
        const hasExpectedContent =
            pageSource.includes('Login') ||
            pageSource.includes('email') ||
            pageSource.includes('password') ||
            pageSource.includes('bootstrap') ||
            pageSource.includes('glass-form');

        assert.ok(hasExpectedContent, 'Expected application content not found on login page');
    });
});
`;

// Replace from the last test block onwards
const lastTestStart = content.lastIndexOf('    // \u2550\u2550\u2550\u2550');
const newContent = content.substring(0, lastTestStart) + newEnd;
fs.writeFileSync('tests/login-tests.js', newContent);
console.log('Patched successfully. New last', newContent.length, 'chars.');
