const { Builder, By, until } = require('selenium-webdriver');
const ExcelJS = require('exceljs');
const path = require('path');

// Generate 300 test cases
function generateTestCases() {
    const testCases = [];

    // Core test cases
    testCases.push({ id: 1, email: '', password: '', expected: 'error', description: 'Empty fields' });
    testCases.push({ id: 2, email: 'invalidemail', password: 'password123', expected: 'error', description: 'Invalid email format' });
    testCases.push({ id: 3, email: 'test@gmail.com', password: '', expected: 'error', description: 'Empty password' });
    testCases.push({ id: 4, email: 'test@gmail.com', password: 'wrongpassword', expected: 'error', description: 'Wrong password format' });
    testCases.push({ id: 5, email: 'validuser@gmail.com', password: 'ValidPassword123!', expected: 'success', description: 'Valid credentials format' });

    // Fill the rest to reach 300 tests (Data-driven approach)
    for (let i = 6; i <= 300; i++) {
        // We simulate a mix of successes and failures based on the index
        const isSuccessCase = (i % 10 === 0);

        testCases.push({
            id: i,
            email: `testuser${i}@gmail.com`,
            password: isSuccessCase ? `ValidPass${i}!@#` : `invalidpass${i}`,
            expected: isSuccessCase ? 'success' : 'error',
            description: `Auto-generated test case ${i} - ${isSuccessCase ? 'Valid' : 'Invalid'} input`
        });
    }

    return testCases;
}

async function runTests() {
    const testCases = generateTestCases();
    const results = [];

    console.log(`Starting execution of ${testCases.length} test cases...`);

    const chrome = require('selenium-webdriver/chrome');
    const options = new chrome.Options();
    options.addArguments('--headless'); // run in headless mode so we don't open 300 windows

    // Initialize the driver (Make sure you have chromedriver installed/available)
    let driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();

    // UPDATE THIS URL to match where your frontend is being served locally
    const targetUrl = 'http://127.0.0.1:5500/frontend/login.html';

    try {
        for (const tc of testCases) {
            console.log(`Running Test Case ${tc.id}: ${tc.description}`);
            let status = 'Failed';
            let actualResult = '';
            const startTime = Date.now();

            try {
                await driver.get(targetUrl);

                // Wait for the form to load
                await driver.wait(until.elementLocated(By.id('loginForm')), 5000);

                // Enter email
                const emailInput = await driver.findElement(By.id('email'));
                await emailInput.clear();
                if (tc.email) await emailInput.sendKeys(tc.email);

                // Enter password
                const passwordInput = await driver.findElement(By.id('password'));
                await passwordInput.clear();
                if (tc.password) await passwordInput.sendKeys(tc.password);

                // Submit form
                const submitBtn = await driver.findElement(By.css('button[type="submit"]'));
                await submitBtn.click();

                // Short wait to let local JS validation or API respond
                await driver.sleep(500);

                // Check local validation errors
                const emailError = await driver.findElement(By.id('emailError')).getText();
                const passwordError = await driver.findElement(By.id('passwordError')).getText();

                if (emailError || passwordError) {
                    actualResult = 'error';
                } else {
                    // Check if window alert exists (failed login from API fallback)
                    try {
                        await driver.wait(until.alertIsPresent(), 1000);
                        let alert = await driver.switchTo().alert();
                        actualResult = 'error';
                        await alert.accept();
                    } catch (e) {
                        // If no alert, and no validation text, assume success (video transition started)
                        actualResult = 'success';
                    }
                }

                // Evaluate pass/fail
                if (actualResult === tc.expected) {
                    status = 'Passed';
                } else {
                    status = 'Failed';
                }

            } catch (err) {
                status = 'Failed';
                actualResult = `Exception: ${err.message}`;
            }

            const executionTime = Date.now() - startTime;

            // Record result
            results.push({
                ...tc,
                actualResult,
                status,
                executionTime: `${executionTime}ms`
            });
        }
    } finally {
        // Close browser after all tests
        await driver.quit();
    }

    // Generate the final Excel report
    await generateExcelReport(results);
}

async function generateExcelReport(results) {
    const workbook = new ExcelJS.Workbook();

    // 1. Summary Sheet
    const summarySheet = workbook.addWorksheet('Summary');
    summarySheet.columns = [
        { header: 'Metric', key: 'metric', width: 30 },
        { header: 'Value', key: 'value', width: 15 }
    ];

    const totalTests = results.length;
    const passedTests = results.filter(r => r.status === 'Passed').length;
    const failedTests = totalTests - passedTests;
    const passPercentage = ((passedTests / totalTests) * 100).toFixed(2);

    summarySheet.addRow({ metric: 'Total Test Cases Executed', value: totalTests });
    summarySheet.addRow({ metric: 'Passed', value: passedTests });
    summarySheet.addRow({ metric: 'Failed', value: failedTests });
    summarySheet.addRow({ metric: 'Pass Percentage', value: `${passPercentage}%` });

    // Format Summary sheet
    summarySheet.getRow(1).font = { bold: true };

    // 2. Details Sheet
    const detailsSheet = workbook.addWorksheet('Test Details');
    detailsSheet.columns = [
        { header: 'Test ID', key: 'id', width: 10 },
        { header: 'Description', key: 'description', width: 40 },
        { header: 'Email Input', key: 'email', width: 30 },
        { header: 'Password Input', key: 'password', width: 20 },
        { header: 'Expected Result', key: 'expected', width: 15 },
        { header: 'Actual Result', key: 'actual', width: 30 },
        { header: 'Status', key: 'status', width: 15 },
        { header: 'Execution Time', key: 'time', width: 15 }
    ];

    // Style header row
    detailsSheet.getRow(1).font = { bold: true };

    results.forEach(r => {
        const row = detailsSheet.addRow({
            id: r.id,
            description: r.description,
            email: r.email,
            password: r.password,
            expected: r.expected,
            actual: r.actualResult,
            status: r.status,
            time: r.executionTime
        });

        // Color coding for status column
        if (r.status === 'Passed') {
            row.getCell('status').font = { color: { argb: 'FF008000' } }; // Green text
        } else {
            row.getCell('status').font = { color: { argb: 'FFFF0000' } }; // Red text
        }
    });

    // Save to file
    const reportPath = path.join(__dirname, 'Test_Report.xlsx');
    await workbook.xlsx.writeFile(reportPath);
    console.log(`\nTest execution complete!`);
    console.log(`Excel report generated successfully at: ${reportPath}`);
}

// Execute
runTests().catch(console.error);
