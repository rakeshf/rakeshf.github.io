const loadAndRenderFilename = (filename) => {
  // Extract date from filename
  const match = filename.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})/);
  if (!match) return "Invalid Date";
  const [ , year, month, day, hour, minute ] = match;
  const d = new Date();
  d.setFullYear(Number(year));
  d.setMonth(Number(month) - 1);
  d.setDate(Number(day));
  d.setHours(Number(hour));
  d.setMinutes(Number(minute));
  d.setSeconds(0);
  d.setMilliseconds(0);
  formatted = d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  }).replace(",", "");  
    document.getElementById("summaryDate").textContent = `📅 F&O Summary for ${formatted}`;
};