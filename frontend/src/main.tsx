import React from "react";
import ReactDOM from "react-dom/client";
import { Toaster } from "sonner";
import App from "@/App";
import { RoleProvider } from "@/context/RoleContext";
import "@/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RoleProvider>
      <App />
      <Toaster theme="dark" position="bottom-right" />
    </RoleProvider>
  </React.StrictMode>,
);