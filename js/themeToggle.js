  const modeToggle = document.getElementById("modeToggle");
  const modeIcon = document.getElementById("modeIcon");

  const setTheme = (theme) => {
    document.documentElement.setAttribute("data-bs-theme", theme);
    localStorage.setItem("theme", theme);
    modeIcon.textContent = theme === "dark" ? "light_mode" : "dark_mode";
  };

  const toggleTheme = () => {
    const current = document.documentElement.getAttribute("data-bs-theme") || "light";
    setTheme(current === "dark" ? "light" : "dark");
  };

  modeToggle.addEventListener("click", toggleTheme);

  // On load: apply saved theme
  const saved = localStorage.getItem("theme") || "light";
  setTheme(saved);