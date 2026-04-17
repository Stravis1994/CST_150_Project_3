// Toggle mobile navigation visibility
const hamburgerBtn = document.getElementById("hamburgerBtn");
const mobileNav = document.getElementById("mobileNav");

if (hamburgerBtn && mobileNav) {
  hamburgerBtn.onclick = () => {
    mobileNav.style.display = mobileNav.style.display === "flex" ? "none" : "flex";
  };
}

const productModal = document.getElementById("productModal");
const productModalImage = document.getElementById("productModalImage");
const productModalMeta = document.getElementById("productModalMeta");
const productModalTitle = document.getElementById("productModalTitle");
const productModalPrice = document.getElementById("productModalPrice");
const productModalForm = document.getElementById("productModalForm");
const productCards = document.querySelectorAll(".product-card-clickable");

function openProductModal(card) {
  if (!productModal || !productModalImage || !productModalMeta || !productModalTitle || !productModalPrice || !productModalForm) {
    return;
  }

  const title = card.dataset.title || "Product";
  const game = card.dataset.game || "";
  const rarity = card.dataset.rarity || "";
  const price = card.dataset.price || "";
  const imageUrl = card.dataset.imageUrl || "";
  const addToCartUrl = card.dataset.addToCartUrl || "";

  productModalImage.src = imageUrl;
  productModalImage.alt = title;
  productModalMeta.textContent = [game, rarity].filter(Boolean).join(" · ");
  productModalTitle.textContent = title;
  productModalPrice.textContent = price ? `$${price}` : "";
  productModalForm.action = addToCartUrl;

  productModal.classList.add("is-open");
  productModal.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
}

function closeProductModal() {
  if (!productModal) {
    return;
  }

  productModal.classList.remove("is-open");
  productModal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
}

productCards.forEach((card) => {
  card.addEventListener("click", (event) => {
    if (event.target.closest("button, form, a, select, input, label")) {
      return;
    }

    openProductModal(card);
  });

  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openProductModal(card);
    }
  });
});

if (productModal) {
  productModal.addEventListener("click", (event) => {
    if (event.target.matches("[data-close-modal]")) {
      closeProductModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && productModal.classList.contains("is-open")) {
      closeProductModal();
    }
  });
}
