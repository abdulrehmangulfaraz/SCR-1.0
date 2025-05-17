/**
 * SCR Platform - Animation and Visual Effects
 * Handles all dynamic UI animations and visual effects throughout the platform
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all animations
    initializeAnimations();
    
    // Add event listeners for animation triggers
    addAnimationTriggers();
    
    // Start background animations
    startBackgroundAnimations();
});

/**
 * Initialize all animations on page load
 */
function initializeAnimations() {
    // Initialize AOS (Animate On Scroll)
    AOS.init({
        duration: 800,
        easing: 'ease',
        once: false,
        mirror: false
    });
    
    // Initialize typing effect for titles
    const typingElements = document.querySelectorAll('.typing-effect');
    typingElements.forEach(element => {
        new Typed(element, {
            strings: element.getAttribute('data-text').split(','),
            typeSpeed: 60,
            backSpeed: 30,
            backDelay: 2000,
            loop: true,
            showCursor: true
        });
    });
    
    // Initialize number counters
    const counterElements = document.querySelectorAll('.counter-number');
    counterElements.forEach(element => {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000; // 2 seconds duration
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
            } else {
                element.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            }
        };
        
        // Start animation when element is in viewport
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(element);
    });
}

/**
 * Add event listeners for animation triggers
 */
function addAnimationTriggers() {
    // Add hover effects to interactive elements
    document.querySelectorAll('.hover-effect').forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.classList.add('animate__animated', 'animate__pulse');
        });
        
        element.addEventListener('mouseleave', function() {
            this.classList.remove('animate__animated', 'animate__pulse');
        });
    });
    
    // Add click animations to buttons
    document.querySelectorAll('.btn:not(.no-animation)').forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('animate__animated', 'animate__headShake');
            setTimeout(() => {
                this.classList.remove('animate__animated', 'animate__headShake');
            }, 1000);
        });
    });
    
    // Add ripple effect to cards
    document.querySelectorAll('.card:not(.no-ripple)').forEach(card => {
        card.addEventListener('click', function(e) {
            // Create ripple element
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            
            // Position the ripple
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            
            // Remove ripple after animation completes
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Animate menu items on hover
    document.querySelectorAll('.navbar-nav .nav-item').forEach((item, index) => {
        item.addEventListener('mouseenter', function() {
            this.classList.add('animate__animated', 'animate__fadeIn');
            this.style.animationDelay = `${index * 0.1}s`;
        });
        
        item.addEventListener('mouseleave', function() {
            this.classList.remove('animate__animated', 'animate__fadeIn');
            this.style.animationDelay = '';
        });
    });
}

/**
 * Start continuous background animations
 */
function startBackgroundAnimations() {
    // Pulse animation for the logo
    const logo = document.querySelector('.navbar-brand i');
    if (logo) {
        setInterval(() => {
            logo.classList.add('pulse');
            setTimeout(() => {
                logo.classList.remove('pulse');
            }, 1000);
        }, 5000);
    }
    
    // Floating animation for dashboard cards
    const floatingElements = document.querySelectorAll('.stat-card');
    floatingElements.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.2}s`;
        card.classList.add('floating');
    });
    
    // Random blinking effect for "hacker-style" elements
    const hackerElements = document.querySelectorAll('.hacker-element');
    hackerElements.forEach(element => {
        setInterval(() => {
            const duration = Math.random() * 200 + 50;
            element.style.animation = `blink ${duration}ms`;
            setTimeout(() => {
                element.style.animation = '';
            }, duration);
        }, Math.random() * 5000 + 2000);
    });
}

/**
 * Radar Scan Animation Controller
 * Controls the radar scanning effect on the scan page
 */
class RadarScan {
    constructor(element) {
        this.radarElement = element;
        this.isActive = false;
        this.interval = null;
        this.rotationDegree = 0;
    }
    
    start() {
        if (this.isActive) return;
        this.isActive = true;
        
        // Reset rotation
        this.rotationDegree = 0;
        
        // Start the rotation animation
        this.interval = setInterval(() => {
            this.rotationDegree = (this.rotationDegree + 1) % 360;
            const lineElement = this.radarElement.querySelector('.radar-line');
            if (lineElement) {
                lineElement.style.transform = `rotate(${this.rotationDegree}deg)`;
            }
            
            // Add ping effect every 180 degrees
            if (this.rotationDegree % 180 === 0) {
                this.ping();
            }
        }, 10);
        
        // Add active class
        this.radarElement.classList.add('active');
    }
    
    stop() {
        if (!this.isActive) return;
        this.isActive = false;
        
        // Stop the rotation animation
        clearInterval(this.interval);
        this.interval = null;
        
        // Remove active class
        this.radarElement.classList.remove('active');
    }
    
    ping() {
        // Create ping element
        const ping = document.createElement('div');
        ping.classList.add('radar-ping');
        this.radarElement.appendChild(ping);
        
        // Remove ping after animation
        setTimeout(() => {
            ping.remove();
        }, 2000);
    }
}

/**
 * Particle Background
 * Creates a hacker-style particle background effect
 */
class ParticleBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50;
        
        // Resize canvas to match parent size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Create particles
        this.createParticles();
        
        // Start animation
        this.animate();
    }
    
    resizeCanvas() {
        const parent = this.canvas.parentElement;
        this.canvas.width = parent.offsetWidth;
        this.canvas.height = parent.offsetHeight;
    }
    
    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: Math.random() * 2 + 1,
                color: '#00ff00',
                speedX: Math.random() * 0.5 - 0.25,
                speedY: Math.random() * 0.5 - 0.25
            });
        }
    }
    
    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // Bounce off edges
            if (particle.x < 0 || particle.x > this.canvas.width) {
                particle.speedX *= -1;
            }
            if (particle.y < 0 || particle.y > this.canvas.height) {
                particle.speedY *= -1;
            }
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = particle.color;
            this.ctx.fill();
        });
        
        // Draw connections between particles
        this.particles.forEach(particleA => {
            this.particles.forEach(particleB => {
                const distance = Math.sqrt(
                    Math.pow(particleA.x - particleB.x, 2) + 
                    Math.pow(particleA.y - particleB.y, 2)
                );
                
                if (distance < 100) {
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(0, 255, 0, ${0.3 - distance/100 * 0.3})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.moveTo(particleA.x, particleA.y);
                    this.ctx.lineTo(particleB.x, particleB.y);
                    this.ctx.stroke();
                }
            });
        });
        
        // Continue animation
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize radar animation when available
document.addEventListener('DOMContentLoaded', function() {
    const radarElement = document.querySelector('.radar-animation');
    if (radarElement) {
        const radar = new RadarScan(radarElement);
        
        // Expose radar to global scope for control from scan.js
        window.radarAnimation = radar;
        
        // Auto-start if on scan page
        if (document.querySelector('.scan-process-container')) {
            radar.start();
        }
    }
    
    // Initialize particle background if canvas exists
    const particleCanvas = document.getElementById('particle-background');
    if (particleCanvas) {
        new ParticleBackground('particle-background');
    }
});
