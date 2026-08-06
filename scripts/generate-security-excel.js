const fs = require('fs');
const ExcelJS = require('exceljs');

async function generateReport() {
    const workbook = new ExcelJS.Workbook();
    
    // Sheet 1: Security Findings (from Semgrep SAST)
    const securitySheet = workbook.addWorksheet('Security Findings');
    securitySheet.columns = [
        { header: 'Severity', key: 'severity', width: 15 },
        { header: 'Vulnerability Type', key: 'type', width: 30 },
        { header: 'File Path', key: 'file', width: 40 },
        { header: 'Line', key: 'line', width: 10 },
        { header: 'Message / Description', key: 'message', width: 60 }
    ];
    securitySheet.getRow(1).font = { bold: true };

    let sastCritical = 0, sastHigh = 0, sastMedium = 0, sastLow = 0;

    try {
        if (fs.existsSync('semgrep-results.json')) {
            const semgrepData = JSON.parse(fs.readFileSync('semgrep-results.json', 'utf8'));
            const findings = semgrepData.results || [];
            
            findings.forEach(finding => {
                let severity = 'Low';
                if (finding.extra && finding.extra.severity) {
                    const sev = finding.extra.severity.toUpperCase();
                    if (sev === 'ERROR') severity = 'High';
                    else if (sev === 'WARNING') severity = 'Medium';
                    else severity = 'Low';
                }
                
                if (severity === 'Critical') sastCritical++;
                else if (severity === 'High') sastHigh++;
                else if (severity === 'Medium') sastMedium++;
                else sastLow++;

                securitySheet.addRow({
                    severity: severity,
                    type: finding.check_id || 'Unknown',
                    file: finding.path,
                    line: finding.start ? finding.start.line : '',
                    message: finding.extra ? finding.extra.message : ''
                });
            });
        } else {
            securitySheet.addRow({ message: 'No Semgrep results found.' });
        }
    } catch (e) {
        console.error("Error parsing Semgrep results:", e);
    }

    // Sheet 2: Endpoint Inventory
    const apiSheet = workbook.addWorksheet('Endpoint Inventory');
    apiSheet.columns = [
        { header: 'Endpoint', key: 'endpoint', width: 40 },
        { header: 'HTTP Method', key: 'method', width: 15 },
        { header: 'Authentication Required', key: 'auth', width: 25 },
        { header: 'Expected Roles', key: 'roles', width: 25 },
        { header: 'Controller/File Path', key: 'file', width: 40 }
    ];
    apiSheet.getRow(1).font = { bold: true };
    apiSheet.addRow({ endpoint: '/api/login', method: 'POST', auth: 'No', roles: 'Any', file: 'backend/main.py' });
    apiSheet.addRow({ endpoint: '/api/user', method: 'GET', auth: 'Yes', roles: 'User, Admin', file: 'backend/main.py' });
    apiSheet.addRow({ endpoint: 'Note: Discover endpoints dynamically to populate fully.', method: '', auth: '', roles: '', file: ''});

    // Sheet 3: Dependency Vulnerabilities (from Trivy)
    const depSheet = workbook.addWorksheet('Dependency Vulnerabilities');
    depSheet.columns = [
        { header: 'Severity', key: 'severity', width: 15 },
        { header: 'Package Name', key: 'pkg', width: 25 },
        { header: 'Installed Version', key: 'version', width: 20 },
        { header: 'Vulnerability ID', key: 'cve', width: 20 },
        { header: 'Title', key: 'title', width: 50 }
    ];
    depSheet.getRow(1).font = { bold: true };

    let depCritical = 0, depHigh = 0, depMedium = 0, depLow = 0;

    try {
        if (fs.existsSync('trivy-results.json')) {
            const trivyData = JSON.parse(fs.readFileSync('trivy-results.json', 'utf8'));
            const results = trivyData.Results || [];
            
            results.forEach(res => {
                if (res.Vulnerabilities) {
                    res.Vulnerabilities.forEach(vuln => {
                        const sev = vuln.Severity || 'LOW';
                        
                        if (sev === 'CRITICAL') depCritical++;
                        else if (sev === 'HIGH') depHigh++;
                        else if (sev === 'MEDIUM') depMedium++;
                        else depLow++;

                        depSheet.addRow({
                            severity: sev,
                            pkg: vuln.PkgName,
                            version: vuln.InstalledVersion,
                            cve: vuln.VulnerabilityID,
                            title: vuln.Title || vuln.Description || 'No title'
                        });
                    });
                }
            });
        } else {
            depSheet.addRow({ title: 'No Trivy results found.' });
        }
    } catch (e) {
        console.error("Error parsing Trivy results:", e);
    }

    // Sheet 4: Risk Summary
    const summarySheet = workbook.addWorksheet('Risk Summary');
    summarySheet.columns = [
        { header: 'Metric', key: 'metric', width: 30 },
        { header: 'Value', key: 'value', width: 20 }
    ];
    summarySheet.getRow(1).font = { bold: true };

    const totalCritical = sastCritical + depCritical;
    const totalHigh = sastHigh + depHigh;
    const totalMedium = sastMedium + depMedium;
    const totalLow = sastLow + depLow;
    
    summarySheet.addRow({ metric: 'Total Critical Findings', value: totalCritical });
    summarySheet.addRow({ metric: 'Total High Findings', value: totalHigh });
    summarySheet.addRow({ metric: 'Total Medium Findings', value: totalMedium });
    summarySheet.addRow({ metric: 'Total Low Findings', value: totalLow });
    summarySheet.addRow({});
    summarySheet.addRow({ metric: 'SAST Critical', value: sastCritical });
    summarySheet.addRow({ metric: 'Dependency Critical', value: depCritical });
    
    // Write File
    await workbook.xlsx.writeFile('Security_Findings.xlsx');
    console.log("Successfully generated Security_Findings.xlsx");
}

generateReport().catch(err => console.error(err));
