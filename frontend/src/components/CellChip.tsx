export default function CellChip({
  code,
  selected,
  onSelect,
}: {
  code: string;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      className={`h-10 rounded-lg border text-xs font-bold transition ${
        selected
          ? "border-accent bg-accent/10 text-accent"
          : "border-line bg-[#0a1b3d]/60 hover:border-accent/50"
      }`}
    >
      {code}
    </button>
  );
}
