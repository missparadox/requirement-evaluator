import { FormEvent, useState } from "react";


export function FileUploadForm() {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement | null;
    if (!input?.files?.length) {
      setError("Select a file before starting evaluation.");
      return;
    }
    setError(null);
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label className="upload-field" htmlFor="requirements-file">
        <span>Requirement File</span>
        <input id="requirements-file" name="file" type="file" />
      </label>
      <button className="upload-button" type="submit">
        Start Evaluation
      </button>
      {error ? <p className="upload-error">{error}</p> : null}
    </form>
  );
}
