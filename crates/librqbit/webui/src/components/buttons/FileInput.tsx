// File-picker and HTML5 drops share validation and batch import feedback.
import { RefObject, useContext, useEffect, useRef, useState } from "react";
import { UploadButton } from "./UploadButton";
import { CgFileAdd } from "react-icons/cg";
import { APIContext } from "../../context";
import { useTorrentStore } from "../../stores/torrentStore";
import { useErrorStore } from "../../stores/errorStore";

export const FileInput = ({ className }: { className?: string }) => {
  const inputRef = useRef<HTMLInputElement>(
    null,
  ) as RefObject<HTMLInputElement>;
  const [file, setFile] = useState<File | null>(null);
  const busy = useRef(false);
  const [progress, setProgress] = useState("");
  const setCloseableError = useErrorStore((state) => state.setCloseableError);

  const API = useContext(APIContext);

  const refreshTorrents = useTorrentStore((state) => state.refreshTorrents);

  const importFiles = async (files: File[]) => {
    if (!files.length) return;
    if (busy.current || file) {
      setCloseableError({
        text: "Finish the current import before adding more files.",
      });
      return;
    }
    const invalid = files.filter(
      (f) => !f.name.toLowerCase().endsWith(".torrent"),
    );
    if (invalid.length) {
      setCloseableError({
        text: `Only .torrent files are supported: ${invalid.map((f) => f.name).join(", ")}`,
      });
      return;
    }
    if (files.length === 1) {
      setFile(files[0]);
    } else {
      busy.current = true;
      setCloseableError(null);
      const failures: string[] = [];
      let added = 0;
      try {
        for (const candidate of files) {
          setProgress(
            `Importing ${added + failures.length + 1} of ${files.length}`,
          );
          try {
            await API.uploadTorrent(candidate, { overwrite: true });
            added++;
          } catch (error) {
            const message =
              error instanceof Error
                ? error.message
                : typeof error === "object" && error !== null && "text" in error
                  ? String(error.text)
                  : String(error);
            failures.push(`${candidate.name}: ${message}`);
          }
        }
      } finally {
        busy.current = false;
        refreshTorrents();
        setProgress(`Processed ${added} of ${files.length} torrents`);
        if (failures.length)
          setCloseableError({
            text: `Failed to import ${failures.length} torrent(s)`,
            details: { text: failures.join("; ") },
          });
      }
    }
  };

  const onFileChange = () => {
    const files = Array.from(inputRef.current?.files ?? []);
    if (inputRef.current) inputRef.current.value = "";
    void importFiles(files);
  };

  useEffect(() => {
    const dragOver = (event: DragEvent) => {
      if (!event.dataTransfer?.types.includes("Files")) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = busy.current || file ? "none" : "copy";
    };
    const drop = (event: DragEvent) => {
      if (!event.dataTransfer?.types.includes("Files")) return;
      event.preventDefault();
      void importFiles(Array.from(event.dataTransfer.files));
    };
    document.addEventListener("dragover", dragOver);
    document.addEventListener("drop", drop);
    return () => {
      document.removeEventListener("dragover", dragOver);
      document.removeEventListener("drop", drop);
    };
  }, [API, file]);

  const reset = () => {
    if (!inputRef?.current) {
      return;
    }
    inputRef.current.value = "";
    setFile(null);
  };

  const onClick = () => {
    if (busy.current || file) return;
    if (!inputRef?.current) {
      return;
    }
    inputRef.current.click();
  };

  return (
    <>
      <input
        type="file"
        ref={inputRef}
        multiple={true}
        accept=".torrent"
        onChange={onFileChange}
        hidden
      />
      <UploadButton
        onClick={onClick}
        data={file}
        resetData={reset}
        className={`group ${className}`}
      >
        <CgFileAdd className="text-blue-500 group-hover:text-white dark:text-white" />
        <div>Upload .torrent File</div>
      </UploadButton>
      {progress && (
        <span role="status" className="text-sm">
          {progress}
        </span>
      )}
    </>
  );
};
