export default function Disclaimer({ text }) {
  return (
    <div className="border border-bear/40 bg-[#1a0a0a] rounded-lg px-4 py-3 text-xs text-bear/80 mb-4">
      ⚠️ <strong>Disclaimer:</strong>{' '}
      {text || 'Market data is delayed. This platform is for research purposes only — not investment advice. Past performance does not guarantee future results.'}
    </div>
  );
}
