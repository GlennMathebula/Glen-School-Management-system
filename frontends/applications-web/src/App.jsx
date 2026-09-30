import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ApplyPage from "./pages/ApplyPage";
import HomePage from "./pages/HomePage";
import RegisterPage from "./pages/RegisterPage";
import StatusPage from "./pages/StatusPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/apply" element={<ApplyPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    </Layout>
  );
}
