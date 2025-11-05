export default function Register() {
  return (
    <div className="max-w-md mx-auto bg-gray-800 p-6 rounded-2xl shadow-lg">
      <h2 className="text-xl font-bold mb-4 text-center">Register</h2>
      <form className="space-y-4">
        <input className="w-full p-2 rounded bg-gray-700" placeholder="Name" />
        <input className="w-full p-2 rounded bg-gray-700" placeholder="Email" />
        <input className="w-full p-2 rounded bg-gray-700" placeholder="Password" type="password" />
        <button className="w-full bg-red-500 py-2 rounded hover:bg-red-600 transition">Register</button>
      </form>
    </div>
  );
}
