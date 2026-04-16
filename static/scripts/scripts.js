// Toggle mobile navigation visibility
document.getElementById("hamburgerBtn").onclick = () => {
  const nav = document.getElementById("mobileNav");
  nav.style.display = nav.style.display === "flex" ? "none" : "flex";
};
