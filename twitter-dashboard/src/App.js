import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import SettingsPage from "./components/SettingsPage";
import TweetsPage from "./components/TweetsPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SettingsPage />} />
        <Route path="/tweets" element={<TweetsPage />} />
      </Routes>
    </Router>
  );
}

export default App;