// Funções JS Globais

// Mostrar/ocultar campos dependendo da seleção
function toggleFieldVisibility() {
    // Para ser usado em múltiplos formulários
    const toggleSelectors = document.querySelectorAll('[data-toggle-target]');
    
    toggleSelectors.forEach(selector => {
        selector.addEventListener('change', function() {
            const targetId = this.dataset.toggleTarget;
            const targetEl = document.getElementById(targetId);
            
            if (targetEl) {
                if (this.checked || this.value === 'true' || this.value === '1') {
                    targetEl.style.display = 'block';
                } else {
                    targetEl.style.display = 'none';
                }
            }
        });
    });
}

// Inicialização quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Inicializar toggle de campos
    toggleFieldVisibility();
});

// Função para copiar texto para a área de transferência
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    
    if (element) {
        navigator.clipboard.writeText(element.innerText || element.value)
            .then(() => {
                // Mostrar feedback visual de sucesso
                const originalText = element.dataset.originalLabel || 'Copiar';
                const originalClass = element.className;
                
                element.textContent = 'Copiado!';
                element.className += ' text-success';
                
                setTimeout(() => {
                    element.textContent = originalText;
                    element.className = originalClass;
                }, 2000);
            })
            .catch(err => {
                console.error('Erro ao copiar texto: ', err);
            });
    }
}
