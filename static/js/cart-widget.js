// Cart Widget - Shows cart items and cost in header
(function() {
    let cartData = { count: 0, total_cost: 0, total_pages: 0 };

    // Create cart button element
    function createCartButton() {
        const existingBtn = document.getElementById('cartButton');
        if (existingBtn) return existingBtn;

        const cartBtn = document.createElement('button');
        cartBtn.id = 'cartButton';
        cartBtn.className = 'cart-button';
        cartBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="9" cy="21" r="1"></circle>
                <circle cx="20" cy="21" r="1"></circle>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
            </svg>
            <span class="cart-count" id="cartCount">0</span>
            <span class="cart-info">
                <span class="cart-items" id="cartItems">0 items</span>
                <span class="cart-price" id="cartPrice">₹0</span>
            </span>
        `;
        
        cartBtn.onclick = function() {
            if (cartData.count > 0) {
                openCartSidebar();
            }
        };

        return cartBtn;
    }

    // Update cart display
    function updateCartDisplay() {
        const countElem = document.getElementById('cartCount');
        const itemsElem = document.getElementById('cartItems');
        const priceElem = document.getElementById('cartPrice');
        const cartBtn = document.getElementById('cartButton');

        if (countElem) {
            countElem.textContent = cartData.count;
            countElem.style.display = cartData.count > 0 ? 'flex' : 'none';
        }
        if (itemsElem) {
            itemsElem.textContent = `${cartData.count} item${cartData.count !== 1 ? 's' : ''}`;
        }
        if (priceElem) {
            priceElem.textContent = `₹${cartData.total_cost}`;
        }
        if (cartBtn) {
            cartBtn.disabled = cartData.count === 0;
            cartBtn.style.opacity = cartData.count === 0 ? '0.6' : '1';
            cartBtn.style.cursor = cartData.count === 0 ? 'not-allowed' : 'pointer';
        }
    }

    // Fetch cart summary from server
    async function fetchCartSummary() {
        try {
            const response = await fetch('/api/cart-summary');
            if (response.ok) {
                cartData = await response.json();
                updateCartDisplay();
                
                // Hide cart button if cart is empty
                const cartBtn = document.getElementById('cartButton');
                if (cartBtn && cartData.count === 0) {
                    cartBtn.style.display = 'none';
                } else if (cartBtn) {
                    cartBtn.style.display = 'flex';
                }
            }
        } catch (error) {
            console.error('Error fetching cart summary:', error);
        }
    }

    // Initialize cart widget
    function initCartWidget() {
        // Find header and add cart button
        const header = document.querySelector('.header');
        if (header) {
            const cartBtn = createCartButton();
            
            // Add cart button to header (align right)
            if (!document.getElementById('cartButton')) {
                header.appendChild(cartBtn);
            }
            
            // Fetch initial cart data on page load only
            fetchCartSummary();
            
            // Cart updates only when explicitly triggered by user actions
            // Call window.refreshCart() after user interactions (uploads, copy changes, etc.)
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCartWidget);
    } else {
        initCartWidget();
    }

    // Expose refresh function globally
    window.refreshCart = fetchCartSummary;

    // Cart sidebar functions
    window.openCartSidebar = function() {
        // Create sidebar if it doesn't exist
        let sidebar = document.getElementById('cartSidebar');
        if (!sidebar) {
            createCartSidebar();
            sidebar = document.getElementById('cartSidebar');
        }
        
        // Load fresh cart items from server when sidebar opens
        loadCartItems();
        
        // Show sidebar
        sidebar.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    window.closeCartSidebar = function() {
        const sidebar = document.getElementById('cartSidebar');
        if (sidebar) {
            sidebar.classList.remove('active');
            document.body.style.overflow = '';
        }
    };

    function createCartSidebar() {
        const sidebar = document.createElement('div');
        sidebar.id = 'cartSidebar';
        sidebar.className = 'payment-sidebar';
        sidebar.innerHTML = `
            <div class="sidebar-overlay" onclick="closeCartSidebar()"></div>
            <div class="sidebar-content">
                <!-- Header -->
                <div class="sidebar-header">
                    <h2>My Cart</h2>
                    <button class="close-btn" onclick="closeCartSidebar()">×</button>
                </div>

                <!-- Cart Items -->
                <div class="sidebar-body">
                    <div class="step-title">
                        <div class="timer-icon">⏱️</div>
                        <div>
                            <h3>Prints in 5 minutes</h3>
                            <p class="step-subtitle">
                                <span id="sidebarTotalPages">0 pages</span>
                                <a href="/checkout" class="edit-link">Edit</a>
                            </p>
                        </div>
                    </div>

                    <!-- Files List -->
                    <div class="files-list" id="sidebarFilesList">
                        <!-- Files will be loaded here -->
                    </div>

                    <!-- QR Code -->
                    <div class="file-name">Pay Here: </div>
                    <div class="qr-section-sidebar">
                        <img src="/static/assets/upi-qr.png" alt="UPI QR Code" class="qr-code-sidebar">
                    </div>

                    <!-- Bill Details -->
                    <div class="bill-details">
                        <h3>Bill details</h3>
                        <div class="bill-row">
                            <span>📋 Items total <span class="saved-badge" id="sidebarSavedBadge">Saved ₹0</span></span>
                            <span><s id="sidebarOriginalPrice">₹0</s> <span id="sidebarItemsTotal">₹0</span></span>
                        </div>
                        <div class="bill-row">
                            <span>💼 Handling charge</span>
                            <span>₹0</span>
                        </div>
                        <div class="bill-row bill-total">
                            <span>Grand total</span>
                            <span id="sidebarGrandTotal">₹0</span>
                        </div>
                    </div>

                    <!-- Cancellation Policy -->
                    <div class="cancellation-policy">
                        <h4>Cancellation Policy</h4>
                        <p>Orders cannot be cancelled once processing for print starts. In case of unexpected issues, a refund will be provided, if applicable.</p>
                    </div>

                    <!-- I Have Paid Button -->
                    <form method="POST" action="/payment" id="cartPaymentForm">
                        <button type="submit" class="upload-screenshot-btn">
                            <span class="btn-amount" id="sidebarBtnAmount">₹2</span>
                            <span class="btn-text">I have paid - Continue ›</span>
                        </button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(sidebar);
    }

    async function loadCartItems() {
        try {
            const response = await fetch('/api/cart-details');
            if (response.ok) {
                const data = await response.json();
                updateSidebarContent(data);
            }
        } catch (error) {
            console.error('Error loading cart items:', error);
        }
    }

    function updateSidebarContent(data) {
        const filesList = document.getElementById('sidebarFilesList');
        const totalPages = document.getElementById('sidebarTotalPages');
        const itemsTotal = document.getElementById('sidebarItemsTotal');
        const originalPrice = document.getElementById('sidebarOriginalPrice');
        const savedBadge = document.getElementById('sidebarSavedBadge');
        const grandTotal = document.getElementById('sidebarGrandTotal');
        const btnAmount = document.getElementById('sidebarBtnAmount');

        // Update pages
        if (totalPages) {
            totalPages.textContent = `${data.total_pages} pages`;
        }

        // Update file list
        if (filesList) {
            filesList.innerHTML = data.jobs.map((job, index) => {
                const copiesText = job.copies > 1 ? `x${job.copies}` : '';
                const copiesBadge = job.copies > 1 ? `<span class="copies-badge">${copiesText}</span>` : '';
                
                // Smart filename truncation (matches Python version)
                const truncateFilename = (filename, maxLength = 20) => {
                    if (filename.length <= maxLength) {
                        return filename;
                    }
                    
                    // Get filename without extension
                    const lastDotIndex = filename.lastIndexOf('.');
                    const name = lastDotIndex > 0 ? filename.substring(0, lastDotIndex) : filename;
                    const extension = lastDotIndex > 0 ? filename.substring(lastDotIndex) : '';
                    
                    // Truncate name only, keep extension
                    const availableLength = maxLength - extension.length - 3; // 3 for "..."
                    if (availableLength > 0) {
                        return name.substring(0, availableLength) + '...' + extension;
                    } else {
                        // Extension too long, truncate everything
                        return filename.substring(0, maxLength - 3) + '...';
                    }
                };
                
                // Calculate individual file cost with copies
                const fileTotal = Math.floor(job.cost);
                // Fake original price: ₹8/page instead of ₹5/page (60% markup)
                const fileOriginal = Math.floor(job.cost * 1.6);
                
                return `
                    <div class="file-item">
                        <div class="file-thumbnail-placeholder">📄</div>
                        <div class="file-details">
                            <div class="file-name">File ${index + 1} - ${truncateFilename(job.filename)} ${copiesBadge}</div>
                            <div class="file-meta">${job.pages} page${job.pages !== 1 ? 's' : ''} ${copiesText ? `× ${job.copies} copies = ${job.pages * job.copies} pages` : ''}, Black & White, Portrait</div>
                            <div class="file-price">₹${fileTotal} <span class="file-price-original">₹${fileOriginal}</span></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Update bill details - data.total_cost already includes all copies
        // Fake discount: show ₹8/page as original (60% markup on ₹5/page)
        const actualTotal = Math.floor(data.total_cost);
        const fakeOriginal = Math.floor(data.total_cost * 1.6);
        const saved = fakeOriginal - actualTotal;
        const grand = actualTotal; // No handling charge, grand total = items total

        if (itemsTotal) itemsTotal.textContent = `₹${actualTotal}`;
        if (originalPrice) originalPrice.textContent = `₹${fakeOriginal}`;
        if (savedBadge) savedBadge.textContent = `Saved ₹${saved}`;
        if (grandTotal) grandTotal.textContent = `₹${grand}`;
        if (btnAmount) btnAmount.textContent = `₹${grand}`;
    }
})();
