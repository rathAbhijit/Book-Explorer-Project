import { useState } from "react";
import { exploreBooks } from "../services/bookApi.js";

export default function Explore() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const search = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await exploreBooks(q);
      setItems(data || []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={search} className="flex gap-2 mb-4">
        <input className="flex-1 p-2 rounded bg-gray-800" placeholder="Search books…"
               value={q} onChange={(e)=>setQ(e.target.value)} />
        <button className="px-4 rounded bg-red-500">{loading ? "..." : "Search"}</button>
      </form>

      {!items.length && !loading && <p className="text-gray-400">Try a search.</p>}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {items.map((b) => (
          <div key={b.google_id} className="bg-gray-800 p-3 rounded">
            <img src={b.thumbnail_url} alt={b.title} className="w-full h-40 object-cover rounded" />
            <div className="mt-2 text-sm font-semibold">{b.title}</div>
            <div className="text-xs text-gray-400">{(b.authors || []).join(", ")}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
