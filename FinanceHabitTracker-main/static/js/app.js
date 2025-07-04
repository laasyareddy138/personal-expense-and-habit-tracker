/**
 * Expense & Habit Tracker - Main JavaScript Application
 * Handles interactive features, animations, and user experience enhancements
 */

// Application configuration
const AppConfig = {
    colors: {
        primary: '#4DB6AC',
        secondary: '#EEEEEE', 
        accent: '#81C784',
        success: '#81C784',
        warning: '#FFB74D',
        danger: '#E57373',
        info: '#64B5F6'
    },
    animations: {
        duration: 300,
        easing: 'ease-in-out'
    }
};

// Main application object
const ExpenseHabitTracker = {
    init() {
        this.initEventListeners();
        this.initAnimations();
        this.initFormValidation();
        this.initTooltips();
        this.initProgressBars();
        this.initHabitInteractions();
        this.initExpenseFeatures();
        this.initGoalFeatures();
        this.initKeyboardShortcuts();
        console.log('Expense & Habit Tracker initialized successfully');
    },

    // Initialize all event listeners
    initEventListeners() {
        // Handle form submissions with loading states
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });

        // Handle modal events
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('shown.bs.modal', this.handleModalShown.bind(this));
            modal.addEventListener('hidden.bs.modal', this.handleModalHidden.bind(this));
        });

        // Handle navigation smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', this.handleSmoothScroll.bind(this));
        });

        // Handle card hover effects
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', this.handleCardHover.bind(this));
            card.addEventListener('mouseleave', this.handleCardLeave.bind(this));
        });

        // Handle button clicks with feedback
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', this.handleButtonClick.bind(this));
        });
    },

    // Initialize animations and transitions
    initAnimations() {
        // Animate cards on page load
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = `all ${AppConfig.animations.duration}ms ${AppConfig.animations.easing}`;
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Animate stats on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateStatNumbers(entry.target);
                }
            });
        });

        document.querySelectorAll('.stat-card h3').forEach(stat => {
            observer.observe(stat);
        });
    },

    // Animate numerical statistics with counting effect
    animateStatNumbers(element) {
        const text = element.textContent;
        const number = parseFloat(text.replace(/[^0-9.-]+/g, ''));
        
        if (isNaN(number)) return;
        
        const prefix = text.match(/^[^0-9.-]*/)?.[0] || '';
        const suffix = text.match(/[^0-9.-]*$/)?.[0] || '';
        
        let current = 0;
        const increment = number / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= number) {
                current = number;
                clearInterval(timer);
            }
            
            element.textContent = prefix + current.toFixed(2) + suffix;
        }, 20);
    },

    // Initialize form validation
    initFormValidation() {
        // Custom validation for expense forms
        const expenseAmountInputs = document.querySelectorAll('input[name="amount"]');
        expenseAmountInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (value < 0) {
                    e.target.setCustomValidity('Amount must be positive');
                    e.target.classList.add('is-invalid');
                } else if (value > 1000000) {
                    e.target.setCustomValidity('Amount seems unusually high. Please verify.');
                    e.target.classList.add('is-invalid');
                } else {
                    e.target.setCustomValidity('');
                    e.target.classList.remove('is-invalid');
                    e.target.classList.add('is-valid');
                }
            });
        });

        // Date validation - prevent future dates for expenses
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (input.closest('#addExpenseModal')) {
                input.addEventListener('change', (e) => {
                    const selectedDate = new Date(e.target.value);
                    const today = new Date();
                    today.setHours(23, 59, 59, 999); // End of today
                    
                    if (selectedDate > today) {
                        e.target.setCustomValidity('Expense date cannot be in the future');
                        e.target.classList.add('is-invalid');
                        this.showToast('Expense date cannot be in the future', 'warning');
                    } else {
                        e.target.setCustomValidity('');
                        e.target.classList.remove('is-invalid');
                    }
                });
            }
        });

        // Goal target date validation
        const goalDateInputs = document.querySelectorAll('#target_date');
        goalDateInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const selectedDate = new Date(e.target.value);
                const today = new Date();
                
                if (selectedDate <= today) {
                    e.target.setCustomValidity('Goal target date should be in the future');
                    e.target.classList.add('is-invalid');
                } else {
                    e.target.setCustomValidity('');
                    e.target.classList.remove('is-invalid');
                }
            });
        });
    },

    // Initialize Bootstrap tooltips
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // Initialize progress bar animations
    initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const progressBar = entry.target;
                    const targetWidth = progressBar.style.width;
                    
                    progressBar.style.width = '0%';
                    setTimeout(() => {
                        progressBar.style.transition = 'width 1s ease-out';
                        progressBar.style.width = targetWidth;
                    }, 200);
                }
            });
        });

        progressBars.forEach(bar => observer.observe(bar));
    },

    // Initialize habit-specific interactions
    initHabitInteractions() {
        // Habit toggle buttons with animations
        const habitToggles = document.querySelectorAll('.habit-toggle');
        habitToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleHabitToggle(toggle);
            });
        });

        // Streak celebrations
        const streakDisplays = document.querySelectorAll('.streak-display');
        streakDisplays.forEach(display => {
            const streakValue = parseInt(display.querySelector('.fw-bold')?.textContent || '0');
            if (streakValue > 0 && streakValue % 7 === 0) {
                display.classList.add('milestone-streak');
                display.title = `${streakValue} day milestone! Keep it up!`;
            }
        });

        // Habit completion rate visual enhancements
        this.updateCircularProgress();
    },

    // Handle habit toggle with smooth animation
    handleHabitToggle(toggle) {
        const icon = toggle.querySelector('i');
        const originalClass = icon.className;
        
        // Show loading animation
        icon.className = 'fas fa-spinner fa-spin';
        toggle.style.opacity = '0.6';
        toggle.style.pointerEvents = 'none';
        
        // Add success animation before navigation
        setTimeout(() => {
            icon.className = 'fas fa-check';
            toggle.style.backgroundColor = AppConfig.colors.success;
            toggle.style.color = 'white';
            
            setTimeout(() => {
                window.location.href = toggle.href;
            }, 300);
        }, 500);
    },

    // Update circular progress indicators
    updateCircularProgress() {
        const progressElements = document.querySelectorAll('.circular-progress');
        progressElements.forEach(element => {
            const percentage = parseFloat(element.dataset.percentage || '0');
            const color = this.getProgressColor(percentage);
            
            // Create visual progress indicator
            element.style.background = `conic-gradient(${color} ${percentage * 3.6}deg, #E0E0E0 0deg)`;
            element.style.border = `3px solid ${color}`;
            
            // Add hover effects
            element.addEventListener('mouseenter', () => {
                element.style.transform = 'scale(1.1)';
                element.style.transition = 'transform 0.3s ease';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = 'scale(1)';
            });
        });
    },

    // Get appropriate color based on progress percentage
    getProgressColor(percentage) {
        if (percentage >= 80) return AppConfig.colors.success;
        if (percentage >= 60) return AppConfig.colors.warning;
        if (percentage >= 40) return AppConfig.colors.info;
        return AppConfig.colors.danger;
    },

    // Initialize expense-specific features
    initExpenseFeatures() {
        // Auto-focus amount input in expense modal
        const expenseModal = document.getElementById('addExpenseModal');
        if (expenseModal) {
            expenseModal.addEventListener('shown.bs.modal', () => {
                const amountInput = document.getElementById('amount');
                if (amountInput) {
                    amountInput.focus();
                    amountInput.select();
                }
            });
        }

        // Set today's date as default for expense date
        const expenseDateInput = document.querySelector('#addExpenseModal input[name="date"]');
        if (expenseDateInput && !expenseDateInput.value) {
            expenseDateInput.value = new Date().toISOString().split('T')[0];
        }

        // Category color coding
        this.initCategoryColors();

        // Expense row hover effects
        const expenseRows = document.querySelectorAll('.expense-row');
        expenseRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.backgroundColor = '#FFF3E0';
                row.style.transform = 'translateX(5px)';
                row.style.transition = 'all 0.3s ease';
            });
            
            row.addEventListener('mouseleave', () => {
                row.style.backgroundColor = '';
                row.style.transform = 'translateX(0)';
            });
        });
    },

    // Initialize category color coding
    initCategoryColors() {
        const categoryBadges = document.querySelectorAll('.badge.bg-secondary');
        const categoryColors = {
            'Food & Dining': '#FF5722',
            'Transportation': '#2196F3',
            'Shopping': '#9C27B0',
            'Entertainment': '#FF9800',
            'Bills & Utilities': '#607D8B',
            'Healthcare': '#F44336',
            'Education': '#3F51B5',
            'Travel': '#00BCD4',
            'Other': '#795548'
        };

        categoryBadges.forEach(badge => {
            const categoryName = badge.textContent.trim();
            const color = categoryColors[categoryName] || AppConfig.colors.secondary;
            badge.style.backgroundColor = color;
            badge.classList.remove('bg-secondary');
        });
    },

    // Initialize goal-specific features
    initGoalFeatures() {
        // Goal progress animation
        const goalCards = document.querySelectorAll('.goal-card');
        goalCards.forEach(card => {
            const progressBar = card.querySelector('.progress-bar');
            if (progressBar) {
                const percentage = parseFloat(progressBar.getAttribute('aria-valuenow'));
                
                // Add milestone indicators
                if (percentage >= 100) {
                    card.classList.add('goal-achieved');
                    this.addAchievementEffect(card);
                } else if (percentage >= 75) {
                    card.classList.add('goal-near-completion');
                }
            }
        });

        // Goal progress form enhancements
        const goalForms = document.querySelectorAll('form[action*="update_goal"]');
        goalForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const amountInput = form.querySelector('input[name="amount"]');
                const amount = parseFloat(amountInput.value);
                
                if (amount <= 0) {
                    e.preventDefault();
                    this.showToast('Please enter a positive amount', 'warning');
                    amountInput.focus();
                }
            });
        });
    },

    // Add achievement effect to completed goals
    addAchievementEffect(card) {
        const trophy = document.createElement('div');
        trophy.innerHTML = '<i class="fas fa-trophy"></i>';
        trophy.className = 'achievement-trophy';
        trophy.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            color: #FFD700;
            font-size: 1.5rem;
            animation: bounce 2s infinite;
            z-index: 10;
        `;
        
        card.style.position = 'relative';
        card.appendChild(trophy);
    },

    // Initialize keyboard shortcuts
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + E for new expense
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const expenseModal = document.getElementById('addExpenseModal');
                if (expenseModal) {
                    new bootstrap.Modal(expenseModal).show();
                }
            }
            
            // Ctrl/Cmd + H for new habit
            if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
                e.preventDefault();
                const habitModal = document.getElementById('addHabitModal');
                if (habitModal) {
                    new bootstrap.Modal(habitModal).show();
                }
            }
            
            // Ctrl/Cmd + G for new goal
            if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
                e.preventDefault();
                const goalModal = document.getElementById('addGoalModal');
                if (goalModal) {
                    new bootstrap.Modal(goalModal).show();
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    bootstrap.Modal.getInstance(modal)?.hide();
                });
            }
        });
    },

    // Handle form submission with loading states
    handleFormSubmit(e) {
        const form = e.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton && !form.checkValidity()) {
            return; // Let browser handle validation
        }
        
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            
            // Re-enable button after delay (in case form doesn't redirect)
            setTimeout(() => {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
            }, 3000);
        }
    },

    // Handle modal shown events
    handleModalShown(e) {
        const modal = e.target;
        const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
        
        if (firstInput) {
            firstInput.focus();
            if (firstInput.type === 'text' || firstInput.type === 'number') {
                firstInput.select();
            }
        }
        
        // Add modal entrance animation
        const modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.transform = 'scale(0.8)';
            modalDialog.style.opacity = '0';
            
            setTimeout(() => {
                modalDialog.style.transition = 'all 0.3s ease-out';
                modalDialog.style.transform = 'scale(1)';
                modalDialog.style.opacity = '1';
            }, 50);
        }
    },

    // Handle modal hidden events
    handleModalHidden(e) {
        const modal = e.target;
        const form = modal.querySelector('form');
        
        if (form) {
            form.reset();
            // Clear validation states
            form.querySelectorAll('.is-valid, .is-invalid').forEach(input => {
                input.classList.remove('is-valid', 'is-invalid');
            });
        }
    },

    // Handle smooth scrolling
    handleSmoothScroll(e) {
        const targetId = e.target.getAttribute('href');
        if (targetId && targetId.startsWith('#')) {
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    },

    // Handle card hover effects
    handleCardHover(e) {
        const card = e.target.closest('.card');
        if (card && !card.classList.contains('no-hover')) {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            card.style.transition = 'all 0.3s ease';
        }
    },

    // Handle card leave events
    handleCardLeave(e) {
        const card = e.target.closest('.card');
        if (card && !card.classList.contains('no-hover')) {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '';
        }
    },

    // Handle button click feedback
    handleButtonClick(e) {
        const button = e.target.closest('.btn');
        if (button && !button.disabled) {
            // Add ripple effect
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.4);
                transform: scale(0);
                animation: ripple-animation 0.6s ease-out;
                pointer-events: none;
            `;
            
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        }
    },

    // Show toast notifications
    showToast(message, type = 'info', duration = 3000) {
        const toastContainer = this.getOrCreateToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${this.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Get or create toast container
    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    },

    // Get appropriate icon for toast type
    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            danger: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    },

    // Utility function to format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Utility function to format dates
    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    },

    // Check if user prefers reduced motion
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
};

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-animation {
        0% {
            transform: scale(0);
            opacity: 1;
        }
        100% {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    .milestone-streak {
        animation: pulse 2s infinite;
    }
    
    .goal-achieved {
        border-left-color: #FFD700 !important;
        background: linear-gradient(135deg, #FFF9C4 0%, #FFFFFF 100%);
    }
    
    .goal-near-completion {
        border-left-color: #FF9800 !important;
    }
    
    .ripple {
        z-index: 1;
    }
    
    .loading {
        opacity: 0.7 !important;
        cursor: wait !important;
    }
`;
document.head.appendChild(style);

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ExpenseHabitTracker.init();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Refresh certain elements when page becomes visible
        const now = new Date().toISOString().split('T')[0];
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (input.closest('#addExpenseModal') && !input.value) {
                input.value = now;
            }
        });
    }
});

// Export for potential module usage
window.ExpenseHabitTracker = ExpenseHabitTracker;
