// Frontend interactions for mobile navigation and product modal behavior.
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

// Populate and display the product quick-view modal from card data attributes.
function openProductModal(card) {
  // Exit safely if modal elements are not present on the current page.
  if (!productModal || !productModalImage || !productModalMeta || !productModalTitle || !productModalPrice || !productModalForm) {
    return;
  }

  // Use dataset values attached to each product card as the source of truth.
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

// Hide the product modal and restore background page scrolling.
function closeProductModal() {
  if (!productModal) {
    return;
  }

  productModal.classList.remove("is-open");
  productModal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
}

// Open the modal from mouse click or keyboard interaction on each card.
productCards.forEach((card) => {
  card.addEventListener("click", (event) => {
    // Do not hijack clicks intended for nested interactive controls.
    if (event.target.closest("button, form, a, select, input, label")) {
      return;
    }

    openProductModal(card);
  });

  card.addEventListener("keydown", (event) => {
    // Support Enter/Space so card activation is keyboard accessible.
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openProductModal(card);
    }
  });
});

if (productModal) {
  // Close when a close-target element is clicked (overlay/button).
  productModal.addEventListener("click", (event) => {
    if (event.target.matches("[data-close-modal]")) {
      closeProductModal();
    }
  });

  // Close with Escape for expected modal keyboard behavior.
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && productModal.classList.contains("is-open")) {
      closeProductModal();
    }
  });
}
