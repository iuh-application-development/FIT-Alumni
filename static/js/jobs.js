/**
 * FIT-Alumni Job Search Page JavaScript
 * Xử lý các chức năng của trang tìm kiếm việc làm
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== Các biến toàn cục =====
    const jobListings = document.querySelector('.job-listings');
    const viewButtons = document.querySelectorAll('.view-btn');
    const advancedFilterToggle = document.getElementById('advancedFilterToggle');
    const advancedFilters = document.getElementById('advancedFilters');
    const loadingContainer = document.querySelector('.loading-container');
    const filterPills = document.querySelectorAll('.filter-pill input[type="radio"]');
    const filterOptions = document.querySelectorAll('.filter-option input[type="radio"]');
    const sortOptions = document.querySelectorAll('.sort-option');
    
    // ===== Xử lý chế độ xem (Grid/List) =====
    initViewMode();
    setupViewToggle();
    
    // ===== Xử lý bộ lọc nâng cao =====
    setupAdvancedFilters();
    
    // ===== Xử lý các radio button =====
    setupFilterPills();
    setupFilterOptions();
    
    // ===== Hiệu ứng cho các tùy chọn sắp xếp =====
    setupSortOptions();
    
    // ===== Hiệu ứng loading =====
    setupLoadingAnimation();
    
    // ===== Hiệu ứng animation khi cuộn =====
    setupScrollAnimation();
    
    /**
     * Khởi tạo chế độ xem dựa trên localStorage
     */
    function initViewMode() {
        const savedView = localStorage.getItem('jobsViewMode');
        if (savedView === 'grid' && jobListings) {
            jobListings.classList.add('grid-view');
            viewButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.view === 'grid') {
                    btn.classList.add('active');
                }
            });
        }
    }
    
    /**
     * Thiết lập sự kiện cho các nút chuyển đổi chế độ xem
     */
    function setupViewToggle() {
        viewButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Loại bỏ lớp active từ tất cả các nút
                viewButtons.forEach(btn => btn.classList.remove('active'));
                
                // Thêm lớp active cho nút được nhấp
                this.classList.add('active');
                
                // Áp dụng chế độ xem tương ứng
                const viewMode = this.dataset.view;
                if (viewMode === 'grid' && jobListings) {
                    jobListings.classList.add('grid-view');
                    localStorage.setItem('jobsViewMode', 'grid');
                } else if (jobListings) {
                    jobListings.classList.remove('grid-view');
                    localStorage.setItem('jobsViewMode', 'list');
                }
            });
        });
    }
    
    /**
     * Thiết lập sự kiện cho bộ lọc nâng cao
     */
    function setupAdvancedFilters() {
        if (advancedFilterToggle && advancedFilters) {
            // Kiểm tra trạng thái đã lưu
            const filtersVisible = localStorage.getItem('advancedFiltersVisible') === 'true';
            
            // Thiết lập trạng thái ban đầu
            if (filtersVisible) {
                advancedFilters.style.display = 'block';
                setTimeout(() => {
                    advancedFilters.classList.add('visible');
                    advancedFilterToggle.classList.add('active');
                }, 10);
                animateFilterGroups();
            }
            
            // Xử lý sự kiện click
            advancedFilterToggle.addEventListener('click', function() {
                if (advancedFilters.classList.contains('visible')) {
                    // Đóng bộ lọc nâng cao với animation
                    advancedFilters.classList.remove('visible');
                    advancedFilterToggle.classList.remove('active');
                    localStorage.setItem('advancedFiltersVisible', 'false');
                    
                    // Đợi animation kết thúc rồi mới ẩn hoàn toàn
                    setTimeout(() => {
                        advancedFilters.style.display = 'none';
                    }, 400); // Thời gian phải khớp với thời gian transition trong CSS
                } else {
                    // Mở bộ lọc nâng cao
                    advancedFilters.style.display = 'block';
                    advancedFilterToggle.classList.add('active');
                    localStorage.setItem('advancedFiltersVisible', 'true');
                    
                    // Đợi một chút để DOM cập nhật, sau đó thêm lớp visible để kích hoạt animation
                    setTimeout(() => {
                        advancedFilters.classList.add('visible');
                        animateFilterGroups();
                    }, 10);
                }
            });
        }
    }
    
    /**
     * Tạo hiệu ứng animation cho các nhóm bộ lọc
     */
    function animateFilterGroups() {
        const filterGroups = document.querySelectorAll('.filter-group');
        filterGroups.forEach((group, index) => {
            group.style.opacity = '0';
            group.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                group.style.transition = 'all 0.5s cubic-bezier(0.165, 0.84, 0.44, 1)';
                group.style.opacity = '1';
                group.style.transform = 'translateY(0)';
            }, 100 * (index + 1));
        });
    }
    
    /**
     * Thiết lập sự kiện cho các filter pill (radio button)
     */
    function setupFilterPills() {
        filterPills.forEach(radio => {
            radio.addEventListener('change', function() {
                // Thêm lớp active cho label chứa radio được chọn
                const allFilterPills = document.querySelectorAll('.filter-pill');
                allFilterPills.forEach(pill => {
                    pill.classList.remove('active');
                });
                this.closest('.filter-pill').classList.add('active');
                
                // Hiển thị hiệu ứng loading
                showLoading();
                
                // Gửi form sau một khoảng thời gian ngắn
                setTimeout(() => {
                    const form = this.closest('form');
                    if (form) form.submit();
                }, 300);
            });
        });
    }
    
    /**
     * Thiết lập sự kiện cho các filter option trong bộ lọc nâng cao
     */
    function setupFilterOptions() {
        filterOptions.forEach(radio => {
            radio.addEventListener('change', function() {
                // Cập nhật trạng thái active cho các option trong cùng nhóm
                const name = this.getAttribute('name');
                const options = document.querySelectorAll(`.filter-option input[name="${name}"]`);
                
                options.forEach(option => {
                    const optionElement = option.closest('.filter-option');
                    if (option.checked) {
                        optionElement.classList.add('active');
                        // Thêm hiệu ứng ripple khi chọn
                        createRippleEffect(optionElement);
                    } else {
                        optionElement.classList.remove('active');
                    }
                });
            });
            
            // Thêm hiệu ứng hover
            const optionElement = radio.closest('.filter-option');
            optionElement.addEventListener('mouseenter', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(-3px)';
                }
            });
            
            optionElement.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(0)';
                }
            });
        });
    }
    
    /**
     * Tạo hiệu ứng ripple khi click vào option
     */
    function createRippleEffect(element) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-effect');
        
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = '0';
        ripple.style.top = '0';
        
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
    
    /**
     * Thiết lập hiệu ứng cho các tùy chọn sắp xếp
     */
    function setupSortOptions() {
        sortOptions.forEach(option => {
            option.addEventListener('mouseenter', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(-3px)';
                }
            });
            
            option.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(0)';
                }
            });
            
            // Hiển thị loading khi click vào tùy chọn sắp xếp
            option.addEventListener('click', function() {
                showLoading();
            });
        });
    }
    
    /**
     * Thiết lập hiệu ứng loading
     */
    function setupLoadingAnimation() {
        if (loadingContainer) {
            // Tạo các phần tử cho hiệu ứng loading
            createLoadingElements();
            
            // Hiển thị loading khi trang đang tải
            showLoading();
            
            // Ẩn loading khi trang đã tải xong
            window.addEventListener('load', function() {
                setTimeout(() => {
                    hideLoading();
                }, 800);
            });
            
            // Hiển thị loading khi form được submit
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', function() {
                    showLoading();
                });
            });
            
            // Hiển thị loading khi click vào các liên kết lọc
            document.querySelectorAll('.filter-tag-remove').forEach(link => {
                link.addEventListener('click', function() {
                    showLoading();
                });
            });
        }
    }
    
    /**
     * Tạo các phần tử cho hiệu ứng loading
     */
    function createLoadingElements() {
        // Thêm thanh tiến trình
        const progressBar = document.createElement('div');
        progressBar.className = 'loading-progress';
        progressBar.innerHTML = '<div class="loading-progress-bar"></div>';
        loadingContainer.appendChild(progressBar);
        
        // Thêm hiệu ứng dots
        const dots = document.createElement('div');
        dots.className = 'loading-dots';
        dots.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
        loadingContainer.appendChild(dots);
    }
    
    /**
     * Hiển thị hiệu ứng loading
     */
    function showLoading() {
        if (loadingContainer) {
            loadingContainer.classList.add('active');
            document.body.style.overflow = 'hidden'; // Ngăn cuộn trang
        }
    }
    
    /**
     * Ẩn hiệu ứng loading
     */
    function hideLoading() {
        if (loadingContainer) {
            loadingContainer.classList.remove('active');
            document.body.style.overflow = ''; // Cho phép cuộn trang
        }
    }
    
    /**
     * Thiết lập hiệu ứng animation khi cuộn trang
     */
    function setupScrollAnimation() {
        const animateOnScroll = function() {
            const elements = document.querySelectorAll('.job-card:not(.animated), .filter-group:not(.animated), .active-filters:not(.animated)');
            
            elements.forEach(element => {
                const elementPosition = element.getBoundingClientRect().top;
                const windowHeight = window.innerHeight;
                
                if (elementPosition < windowHeight - 50) {
                    element.classList.add('animated');
                }
            });
        };
        
        // Chạy animation khi trang tải xong và khi cuộn
        window.addEventListener('scroll', animateOnScroll);
        
        // Chạy một lần khi trang tải xong
        setTimeout(animateOnScroll, 100);
    }
}); 