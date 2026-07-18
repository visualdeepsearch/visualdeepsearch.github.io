const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      entry.target
        .querySelectorAll("[data-chart]")
        .forEach((chart) => chart.classList.add("active"));
    });
  },
  { threshold: 0.12 },
);

document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

document.getElementById("copyBib").addEventListener("click", async (event) => {
  const text = document.querySelector(".citation-box code").textContent;
  await navigator.clipboard.writeText(text);
  event.currentTarget.textContent = "Copied!";
  setTimeout(() => {
    event.currentTarget.textContent = "Copy";
  }, 1600);
});
