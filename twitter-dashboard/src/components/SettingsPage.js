import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function SettingsPage() {
  const [settings, setSettings] = useState({
    TWITTER_BEARER_TOKEN: "",
    NICHE: "",
    STYLE: "",
    BRAND_NAME: "",
  });

  const navigate = useNavigate();

  const handleChange = (e) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const handleSubmit = () => {
    localStorage.setItem("settings", JSON.stringify(settings));
    navigate("/tweets");
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-gray-100">
      <h1 className="text-xl font-bold mb-4">Settings</h1>
      <input
        type="password"
        name="TWITTER_BEARER_TOKEN"
        placeholder="Twitter Bearer Token"
        onChange={handleChange}
        className="p-2 border rounded mb-2 w-80"
      />
      <input
        type="text"
        name="NICHE"
        placeholder="Niche"
        onChange={handleChange}
        className="p-2 border rounded mb-2 w-80"
      />
      <input
        type="text"
        name="STYLE"
        placeholder="Style"
        onChange={handleChange}
        className="p-2 border rounded mb-2 w-80"
      />
      <input
        type="text"
        name="BRAND_NAME"
        placeholder="Brand Name"
        onChange={handleChange}
        className="p-2 border rounded mb-2 w-80"
      />
      <button onClick={handleSubmit} className="bg-blue-500 text-white p-2 rounded mt-2">
        Continue
      </button>
    </div>
  );
}

export default SettingsPage;
