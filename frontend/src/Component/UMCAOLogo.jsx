import React from "react";
import "../CSS/UMCAOLogo.css";
import logo from "../assets/UMCAO.png";

export default function UMCAOLogo({ onClick }) {
  return (
    <button
      type="button"
      className="umcao-logo"
      onClick={onClick || (() => {
        window.location.href = "/";
      })}
      aria-label="UMCAO home"
      title="Go to UMCAO home"
    >
      <img
        src={logo}
        alt="UMCAO - Universal Multi-Language Code Analyzer and Optimizer"
        className="umcao-logo-image"
      />
    </button>
  );
}
