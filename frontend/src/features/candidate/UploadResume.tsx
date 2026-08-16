import { useState } from "react";

export default function UploadResume() {
  const [fileName, setFileName] = useState<string>("");

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Upload Resume</h1>
          <p>Upload your latest resume before applying.</p>
        </div>
      </div>

      <div className="panel form-panel">
        <label>
          Resume File (.pdf, .docx, .txt)
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(event) => {
              const file = event.target.files?.[0];
              setFileName(file ? file.name : "");
            }}
          />
        </label>

        <div className="upload-status">
          {fileName ? (
            <span>Selected file: {fileName}</span>
          ) : (
            <span>No file selected yet.</span>
          )}
        </div>

        <button type="button" className="primary-button" disabled={!fileName}>
          Upload Resume
        </button>
      </div>
    </div>
  );
}
