import React, { useState } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('fields');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      if (selectedFile.type !== 'application/pdf') {
        setError('Please select a valid PDF file.');
        setFile(null);
        return;
      }

      setError(null);
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select an RFP PDF file first.');
      return;
    }

    setLoading(true);
    setError(null);
    setExtractedData(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/extract', {
        method: 'POST',
        headers: {
          accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(
          errData.detail || 'Failed to extract RFP fields.'
        );
      }

      const result = await response.json();
      setExtractedData(result);
      setActiveTab('fields');
    } catch (err) {
      setError(
        err.message || 'Error connecting to the model endpoint.'
      );
    } finally {
      setLoading(false);
    }
  };

  const formatKey = (key) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const fields = extractedData?.extracted_fields || {};

  const foundCount = Object.values(fields).filter(
    (value) =>
      value !== null &&
      value !== undefined &&
      value !== '' &&
      value !== 'تعذر استخراج القيمة'
  ).length;

  const totalFields = Object.keys(fields).length;

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(
        JSON.stringify(fields, null, 2)
      );
    } catch {
      // Keep UI unaffected if clipboard is unavailable.
    }
  };

  const downloadPdf = () => {
  const rows = Object.entries(fields)
    .map(([key, value]) => {
      const formattedValue =
        value === null || value === undefined || value === ''
          ? 'Not found in document'
          : typeof value === 'object'
            ? JSON.stringify(value, null, 2)
            : String(value);

      return `
        <tr>
          <td>${formatKey(key)}</td>
          <td>${formattedValue.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</td>
        </tr>
      `;
    })
    .join('');

  const pdfWindow = window.open('', '_blank');

  if (!pdfWindow) {
    setError('Please allow pop-ups to generate the PDF.');
    return;
  }

  pdfWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8" />
      <title>RFP Extraction Report</title>

      <style>
        @page {
          size: A4;
          margin: 18mm;
        }

        body {
          font-family: Arial, sans-serif;
          color: #1e293b;
          margin: 0;
          padding: 0;
        }

        .header {
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 14px;
          margin-bottom: 20px;
        }

        h1 {
          margin: 0;
          font-size: 22px;
          color: #1f2937;
        }

        .subtitle {
          margin-top: 6px;
          color: #64748b;
          font-size: 12px;
        }

        .meta {
          margin-bottom: 18px;
          font-size: 12px;
          color: #64748b;
        }

        .success {
          display: inline-block;
          margin-top: 8px;
          padding: 4px 9px;
          border-radius: 20px;
          background: #dcfce7;
          color: #166534;
          font-size: 11px;
          font-weight: bold;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
        }

        th,
        td {
          border: 1px solid #dbe3ec;
          padding: 10px;
          vertical-align: top;
          text-align: left;
          font-size: 11px;
          line-height: 1.5;
          word-wrap: break-word;
        }

        th {
          background: #f8fafc;
          font-weight: bold;
        }

        td:first-child {
          width: 30%;
          background: #f8fafc;
          font-weight: bold;
          color: #475569;
        }

        td:nth-child(2) {
          color: #1e293b;
        }

        .footer {
          margin-top: 20px;
          font-size: 10px;
          color: #94a3b8;
        }
      </style>
    </head>

    <body>

      <div class="header">
        <h1>RFP Extraction Assistant</h1>
        <div class="subtitle">
          Extracted information from RFP document
        </div>

        <div class="success">
          ${foundCount} of ${totalFields} fields found
        </div>
      </div>

      <div class="meta">
        ${
          extractedData.latency_seconds !== undefined &&
          extractedData.latency_seconds !== null
            ? `Latency: ${extractedData.latency_seconds}s`
            : ''
        }

        ${
          extractedData.tokens_used !== undefined &&
          extractedData.tokens_used !== null
            ? ` &nbsp;&nbsp; | &nbsp;&nbsp; Tokens: ${extractedData.tokens_used}`
            : ''
        }
      </div>

      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Extracted Value</th>
          </tr>
        </thead>

        <tbody>
          ${rows}
        </tbody>
      </table>

      <div class="footer">
        Generated by RFP Extraction Assistant
      </div>

    </body>
    </html>
  `);

  pdfWindow.document.close();

  pdfWindow.onload = () => {
    pdfWindow.focus();
    pdfWindow.print();
  };
};

  return (
    <>
      <style>{`
        * {
          box-sizing: border-box;
        }

        html,
        body,
        #root {
          width: 100%;
          height: 100%;
          margin: 0;
        }

        body {
          font-family:
            Inter,
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
          background: #eef2f7;
          color: #172033;
        }

        button,
        input {
          font: inherit;
        }

        .app {
          min-height: 100vh;
          background: #eef2f7;
        }

        /* =========================
           HEADER
        ========================== */

        .header {
          height: 72px;
          padding: 0 28px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: #ffffff;
          border-bottom: 1px solid #dce3ec;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 11px;
        }

        .brand-icon {
          width: 30px;
          height: 30px;
          border-radius: 7px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #1f2937;
          color: white;
          font-size: 11px;
          font-weight: 800;
        }

        .brand-title {
          margin: 0;
          color: #1f2937;
          font-size: 17px;
          font-weight: 700;
          letter-spacing: -0.2px;
        }

        .metrics-button {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border: 1px solid #d9e1ea;
          border-radius: 9px;
          background: #ffffff;
          color: #475569;
          font-size: 12px;
          font-weight: 600;
        }

        .metrics-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 0 3px #dcfce7;
        }

        /* =========================
           MAIN LAYOUT
        ========================== */

        .content {
          height: calc(100vh - 72px);
          padding: 34px;
          overflow: hidden;
        }

        .workspace {
          height: 100%;
          max-width: 1400px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 300px minmax(0, 1fr);
          gap: 18px;
        }

        /* =========================
           LEFT PANEL
        ========================== */

        .document-card {
          height: fit-content;
          background: #ffffff;
          border: 1px solid #dbe3ec;
          border-radius: 12px;
          padding: 18px;
          box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        }

        .card-title {
          margin: 0 0 8px;
          color: #1f2937;
          font-size: 13px;
          font-weight: 700;
        }

        .card-description {
          margin: 0 0 18px;
          color: #64748b;
          font-size: 12px;
          line-height: 1.55;
        }

        .upload-box {
          position: relative;
          min-height: 235px;
          border: 1px solid #ccd7e4;
          border-radius: 10px;
          background: #f8fafc;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 18px;
          text-align: center;
          overflow: hidden;
          transition: border-color 0.2s ease;
        }

        .upload-box:hover {
          border-color: #93a4b8;
        }

        .upload-input {
          position: absolute;
          inset: 0;
          opacity: 0;
          cursor: pointer;
        }

        .document-icon {
          width: 50px;
          height: 50px;
          margin-bottom: 14px;
          border-radius: 10px;
          background: #ffffff;
          border: 1px solid #dbe3ec;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 23px;
        }

        .drop-title {
          margin: 0 0 5px;
          color: #475569;
          font-size: 12px;
          font-weight: 600;
        }

        .drop-subtitle {
          margin: 0;
          color: #94a3b8;
          font-size: 11px;
        }

        .file-selected {
          width: 100%;
          padding: 11px;
          border-radius: 8px;
          background: #ffffff;
          border: 1px solid #d8e1eb;
        }

        .file-name {
          margin: 0 0 5px;
          color: #334155;
          font-size: 12px;
          font-weight: 700;
          line-height: 1.4;
          overflow-wrap: anywhere;
        }

        .file-size {
          margin: 0;
          color: #94a3b8;
          font-size: 10px;
        }

        .extract-button {
          width: 100%;
          margin-top: 12px;
          height: 38px;
          border: none;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 700;
          transition: all 0.2s ease;
        }

        .extract-button.active {
          background: #304fce;
          color: white;
          cursor: pointer;
        }

        .extract-button.active:hover {
          background: #2744b6;
        }

        .extract-button.disabled {
          background: #e3e8ef;
          color: #9aa6b5;
          cursor: not-allowed;
        }

        .error {
          margin-top: 12px;
          padding: 10px 11px;
          border: 1px solid #fecaca;
          border-radius: 8px;
          background: #fff5f5;
          color: #b91c1c;
          font-size: 11px;
          line-height: 1.5;
        }

        /* =========================
           RIGHT PANEL
        ========================== */

        .results-card {
          height: 100%;
          min-width: 0;
          background: #ffffff;
          border: 1px solid #dbe3ec;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
          display: flex;
          flex-direction: column;
        }

        .results-header {
          padding: 18px 20px 13px;
          border-bottom: 1px solid #e5eaf0;
        }

        .results-header-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }

        .results-title {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .results-title h2 {
          margin: 0;
          color: #334155;
          font-size: 15px;
          font-weight: 700;
        }

        .found-badge {
          padding: 4px 8px;
          border-radius: 999px;
          background: #dcfce7;
          color: #15803d;
          font-size: 10px;
          font-weight: 700;
          white-space: nowrap;
        }

        .action-group {
          display: flex;
          align-items: center;
          gap: 7px;
          flex-wrap: wrap;
        }

        .tabs {
          display: flex;
          align-items: center;
          padding: 3px;
          border: 1px solid #dce3eb;
          border-radius: 8px;
          background: #f8fafc;
        }

        .tab {
          border: none;
          background: transparent;
          color: #64748b;
          padding: 6px 11px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
        }

        .tab.active {
          background: #ffffff;
          color: #334155;
          box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        }

        .tool-button {
          height: 31px;
          padding: 0 10px;
          border: 1px solid #dce3eb;
          border-radius: 7px;
          background: #ffffff;
          color: #475569;
          font-size: 10px;
          font-weight: 600;
          cursor: pointer;
        }

        .tool-button:hover {
          background: #f8fafc;
        }

        .results-meta {
          display: flex;
          align-items: center;
          gap: 14px;
          margin-top: 11px;
          color: #64748b;
          font-size: 10px;
        }

        .meta-item strong {
          color: #334155;
        }

        .table-container {
          flex: 1;
          overflow: auto;
        }

        .table {
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
        }

        .table tr {
          border-bottom: 1px solid #e6ebf0;
        }

        .table tr:last-child {
          border-bottom: none;
        }

        .table-label {
          width: 30%;
          padding: 13px 18px;
          vertical-align: top;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          line-height: 1.45;
          border-right: 1px solid #edf1f5;
        }

        .table-value {
          padding: 13px 18px;
          vertical-align: top;
          color: #334155;
          font-size: 11px;
          line-height: 1.6;
          overflow-wrap: anywhere;
        }

        .empty-value {
          color: #a0aaba;
          font-style: italic;
        }

        .json-view {
          flex: 1;
          overflow: auto;
          background: #111827;
          padding: 20px;
        }

        .json-view pre {
          margin: 0;
          color: #d7e3ef;
          font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            Menlo,
            monospace;
          font-size: 11px;
          line-height: 1.65;
          white-space: pre-wrap;
          word-break: break-word;
        }

        /* =========================
           LOADING / EMPTY
        ========================== */

        .state {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 30px;
        }

        .state-inner {
          width: 100%;
          max-width: 420px;
        }

        .state-icon {
          width: 68px;
          height: 68px;
          margin: 0 auto 14px;
          border-radius: 12px;
          background: #ffffff;
          border: 1px solid #dbe3ec;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
        }

        .state-title {
          margin: 0;
          color: #475569;
          font-size: 14px;
          font-weight: 700;
        }

        .state-description {
          margin: 6px 0 0;
          color: #94a3b8;
          font-size: 11px;
          line-height: 1.5;
        }

        .loading-spinner {
          width: 36px;
          height: 36px;
          margin: 0 auto 16px;
          border: 3px solid #dbe7ff;
          border-top-color: #304fce;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        /* =========================
           RESPONSIVE
        ========================== */

        @media (max-width: 1000px) {
          .workspace {
            grid-template-columns: 260px minmax(0, 1fr);
          }

          .content {
            padding: 22px;
          }

          .results-header-row {
            align-items: flex-start;
            flex-direction: column;
          }
        }

        @media (max-width: 760px) {
          .header {
            padding: 0 16px;
          }

          .content {
            height: auto;
            min-height: calc(100vh - 72px);
            overflow: visible;
            padding: 16px;
          }

          .workspace {
            height: auto;
            grid-template-columns: 1fr;
          }

          .document-card {
            height: auto;
          }

          .results-card {
            height: 650px;
          }

          .table-label {
            width: 38%;
          }
        }
      `}</style>

      <div className="app">

        {/* =========================
            HEADER
        ========================== */}

        <header className="header">
          <div className="brand">
            <div className="brand-icon">AI</div>

            <h1 className="brand-title">
              RFP Extraction Assistant
            </h1>
          </div>

          <div className="metrics-button">
            <span className="metrics-dot"></span>
            System metrics
            <span style={{ fontSize: 11 }}>↗</span>
          </div>
        </header>


        {/* =========================
            MAIN
        ========================== */}

        <main className="content">
          <div className="workspace">

            {/* =========================
                DOCUMENT
            ========================== */}

            <section className="document-card">

              <h2 className="card-title">
                Document
              </h2>

              <p className="card-description">
                Upload an RFP as a PDF. The local model reads it and
                returns the 17 core schema fields.
              </p>

              <form onSubmit={handleSubmit}>

                <div className="upload-box">

                  <input
                    className="upload-input"
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                  />

                  <div className="document-icon">
                    📄
                  </div>

                  {file ? (
                    <div className="file-selected">
                      <p className="file-name">
                        {file.name}
                      </p>

                      <p className="file-size">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  ) : (
                    <>
                      <p className="drop-title">
                        Choose an RFP PDF
                      </p>

                      <p className="drop-subtitle">
                        Click to select a document
                      </p>
                    </>
                  )}

                </div>

                <button
                  type="submit"
                  disabled={!file || loading}
                  className={`extract-button ${
                    !file || loading
                      ? 'disabled'
                      : 'active'
                  }`}
                >
                  {loading
                    ? 'Processing Document...'
                    : 'Extract data'}
                </button>

              </form>

              {error && (
                <div className="error">
                  <strong>Error:</strong> {error}
                </div>
              )}

            </section>


            {/* =========================
                RESULTS
            ========================== */}

            <section className="results-card">

              {!extractedData && !loading && (
                <div className="state">
                  <div className="state-inner">

                    <div className="state-icon">
                      📥
                    </div>

                    <p className="state-title">
                      No document processed yet
                    </p>

                    <p className="state-description">
                      Upload an RFP PDF from the Document panel
                      to extract its structured fields.
                    </p>

                  </div>
                </div>
              )}


              {loading && (
                <div className="state">
                  <div className="state-inner">

                    <div className="loading-spinner"></div>

                    <p className="state-title">
                      Running AI Inference...
                    </p>

                    <p className="state-description">
                      The local model is reading and extracting
                      information from your RFP.
                    </p>

                  </div>
                </div>
              )}


              {extractedData && (
                <>
                  {/* Results Header */}

                  <div className="results-header">

                    <div className="results-header-row">

                      <div className="results-title">

                        <h2>
                          Extracted fields
                        </h2>

                        <span className="found-badge">
                          {foundCount} of {totalFields} found
                        </span>

                      </div>

                      <div className="action-group">

                        <div className="tabs">

                          <button
                            type="button"
                            className={`tab ${
                              activeTab === 'fields'
                                ? 'active'
                                : ''
                            }`}
                            onClick={() =>
                              setActiveTab('fields')
                            }
                          >
                            Fields
                          </button>

                          <button
                            type="button"
                            className={`tab ${
                              activeTab === 'json'
                                ? 'active'
                                : ''
                            }`}
                            onClick={() =>
                              setActiveTab('json')
                            }
                          >
                            JSON
                          </button>

                        </div>

                        <button
                          type="button"
                          className="tool-button"
                          onClick={copyJson}
                        >
                          ⧉ Copy JSON
                        </button>

                        <button
                          type="button"
                          className="tool-button"
                          onClick={downloadPdf}
                        >
                          ↓ Download PDF
                        </button>

                      </div>

                    </div>


                    <div className="results-meta">

                      {extractedData.latency_seconds !== undefined &&
                        extractedData.latency_seconds !== null && (
                          <div className="meta-item">
                            ⏱ Latency:{' '}
                            <strong>
                              {extractedData.latency_seconds}s
                            </strong>
                          </div>
                        )}

                      {extractedData.tokens_used !== undefined &&
                        extractedData.tokens_used !== null && (
                          <div className="meta-item">
                            🪙 Tokens:{' '}
                            <strong>
                              {extractedData.tokens_used}
                            </strong>
                          </div>
                        )}

                    </div>

                  </div>


                  {/* =========================
                      FIELDS VIEW
                  ========================== */}

                  {activeTab === 'fields' && (
                    <div className="table-container">

                      <table className="table">

                        <tbody>

                          {Object.entries(fields).map(
                            ([key, value]) => (
                              <tr key={key}>

                                <td className="table-label">
                                  {formatKey(key)}
                                </td>

                                <td className="table-value">

                                  {value === null ||
                                  value === undefined ||
                                  value === '' ? (
                                    <span className="empty-value">
                                      Not found in document
                                    </span>
                                  ) : typeof value === 'object' ? (
                                    <pre
                                      style={{
                                        margin: 0,
                                        whiteSpace: 'pre-wrap',
                                        fontFamily:
                                          'monospace',
                                        fontSize: 10,
                                      }}
                                    >
                                      {JSON.stringify(
                                        value,
                                        null,
                                        2
                                      )}
                                    </pre>
                                  ) : (
                                    String(value)
                                  )}

                                </td>

                              </tr>
                            )
                          )}

                        </tbody>

                      </table>

                    </div>
                  )}


                  {/* =========================
                      JSON VIEW
                  ========================== */}

                  {activeTab === 'json' && (
                    <div className="json-view">
                      <pre>
                        {JSON.stringify(
                          fields,
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  )}

                </>
              )}

            </section>

          </div>
        </main>

      </div>
    </>
  );
}