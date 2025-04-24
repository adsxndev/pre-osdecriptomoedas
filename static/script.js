document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const symbolSelect = document.getElementById('symbol-select');
    const customSymbol = document.getElementById('custom-symbol');
    const compareButton = document.getElementById('compare-button');
    const refreshButton = document.getElementById('refresh-button');
    const symbolTitle = document.getElementById('symbol-title');
    const lastUpdated = document.getElementById('last-updated');
    const spotTableBody = document.getElementById('spot-price-table-body');
    const futuresTableBody = document.getElementById('futures-price-table-body');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const themeSwitch = document.getElementById('theme-switch');
    
    // State
    let currentSymbol = 'BTCUSDT';
    let refreshInterval;

    // Translations and language
    const translations = {
        last_updated: "Last Updated:",
        best_price: "Best Price",
        error: "An error occurred while fetching data."
    };
    let currentLang = 'en-US'; // Default to English US.  Could be dynamically set based on user preference or browser setting.
    
    // Initialize
    fetchPrices();
    startAutoRefresh();
    
    // Event listeners
    symbolSelect.addEventListener('change', function() {
        customSymbol.value = '';
        currentSymbol = this.value;
    });
    
    customSymbol.addEventListener('input', function() {
        if (this.value) {
            currentSymbol = this.value.toUpperCase();
        } else {
            currentSymbol = symbolSelect.value;
        }
    });
    
    compareButton.addEventListener('click', function() {
        fetchPrices();
    });
    
    refreshButton.addEventListener('click', function() {
        fetchPrices();
    });
    
    // Theme toggle
    themeSwitch.addEventListener('change', function() {
        const theme = this.checked ? 'dark' : 'light';
        window.location.href = `/set_theme/${theme}`;
    });
    
    function startAutoRefresh() {
        // Refresh every 30 seconds
        refreshInterval = setInterval(fetchPrices, 10000);
    }
    
    function stopAutoRefresh() {
        clearInterval(refreshInterval);
    }
    
    function fetchPrices() {
        showLoading(true);
        hideError();
        
        fetch(`/api/prices?symbol=${currentSymbol}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                updateUI(data);
                showLoading(false);
            })
            .catch(error => {
                showError(translations.error);
                console.error('Error:', error);
                showLoading(false);
            });
    }
    
    function updateUI(data) {
        const { prices, timestamp } = data;
        
        // Update title and timestamp
        symbolTitle.textContent = `${currentSymbol}`;
        const date = new Date(timestamp);
        lastUpdated.textContent = `${translations.last_updated} ${date.toLocaleTimeString()}`;
        
        // Clear previous data
        spotTableBody.innerHTML = '';
        futuresTableBody.innerHTML = '';
        
        // Update tables
        Object.entries(prices).forEach(([exchange, data]) => {
            // Spot table row
            const spotRow = document.createElement('tr');
            
            // Exchange name with link
            const spotExchangeCell = document.createElement('td');
            if (data.spot_url) {
                const exchangeLink = document.createElement('a');
                exchangeLink.href = data.spot_url;
                exchangeLink.textContent = exchange;
                exchangeLink.target = "_blank";
                exchangeLink.rel = "noopener noreferrer";
                spotExchangeCell.appendChild(exchangeLink);
            } else {
                spotExchangeCell.textContent = exchange;
            }
            spotExchangeCell.style.fontWeight = '500';
            spotRow.appendChild(spotExchangeCell);
            
            // Spot price
            const spotPriceCell = document.createElement('td');
            if (data.spot && data.spot.price !== undefined) {
                spotPriceCell.textContent = formatPrice(data.spot.price);
            } else {
                spotPriceCell.textContent = 'N/A';
                spotPriceCell.style.color = 'var(--text-muted)';
            }
            spotRow.appendChild(spotPriceCell);
            
            // Spot difference
            const spotDiffCell = document.createElement('td');
            if (data.spot && data.spot.price !== undefined && data.spot_lowest !== null) {
                const diffSpan = document.createElement('span');
                diffSpan.className = 'price-difference';
                
                if (data.spot.price === data.spot_lowest) {
                    diffSpan.classList.add('best-price');
                    diffSpan.textContent = translations.best_price;
                } else {
                    diffSpan.classList.add('other-price');
                    const percentDiff = ((data.spot.price - data.spot_lowest) / data.spot_lowest) * 100;
                    diffSpan.textContent = `+${percentDiff.toFixed(2)}%`;
                }
                
                spotDiffCell.appendChild(diffSpan);
            } else {
                spotDiffCell.textContent = '-';
                spotDiffCell.style.color = 'var(--text-muted)';
            }
            spotRow.appendChild(spotDiffCell);
            
            spotTableBody.appendChild(spotRow);
            
            // Futures table row
            const futuresRow = document.createElement('tr');
            
            // Exchange name with link
            const futuresExchangeCell = document.createElement('td');
            if (data.futures_url) {
                const exchangeLink = document.createElement('a');
                exchangeLink.href = data.futures_url;
                exchangeLink.textContent = exchange;
                exchangeLink.target = "_blank";
                exchangeLink.rel = "noopener noreferrer";
                futuresExchangeCell.appendChild(exchangeLink);
            } else {
                futuresExchangeCell.textContent = exchange;
            }
            futuresExchangeCell.style.fontWeight = '500';
            futuresRow.appendChild(futuresExchangeCell);
            
            // Futures price
            const futuresPriceCell = document.createElement('td');
            if (data.futures && data.futures.price !== undefined) {
                futuresPriceCell.textContent = formatPrice(data.futures.price);
            } else {
                futuresPriceCell.textContent = 'N/A';
                futuresPriceCell.style.color = 'var(--text-muted)';
            }
            futuresRow.appendChild(futuresPriceCell);
            
            // Futures difference
            const futuresDiffCell = document.createElement('td');
            if (data.futures && data.futures.price !== undefined && data.futures_lowest !== null) {
                const diffSpan = document.createElement('span');
                diffSpan.className = 'price-difference';
                
                if (data.futures.price === data.futures_lowest) {
                    diffSpan.classList.add('best-price');
                    diffSpan.textContent = translations.best_price;
                } else {
                    diffSpan.classList.add('other-price');
                    const percentDiff = ((data.futures.price - data.futures_lowest) / data.futures_lowest) * 100;
                    diffSpan.textContent = `+${percentDiff.toFixed(2)}%`;
                }
                
                futuresDiffCell.appendChild(diffSpan);
            } else {
                futuresDiffCell.textContent = '-';
                futuresDiffCell.style.color = 'var(--text-muted)';
            }
            futuresRow.appendChild(futuresDiffCell);
            
            futuresTableBody.appendChild(futuresRow);
        });
    }
    
    function formatPrice(price) {
        if (price > 1000) {
            return price.toLocaleString(currentLang, {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        } else if (price > 1) {
            return price.toLocaleString(currentLang, {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 4
            });
        } else {
            return price.toLocaleString(currentLang, {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2,
                maximumFractionDigits: 8
            });
        }
    }
    
    function showLoading(isLoading) {
        if (isLoading) {
            loadingIndicator.classList.remove('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }
    
    function hideError() {
        errorMessage.classList.add('hidden');
    }
});
