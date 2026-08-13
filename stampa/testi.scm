; Sostituisce i livelli di testo rasterizzati con veri livelli di testo modificabili.
; La posizione viene ricavata dal livello raster esistente, cosi' l'impaginazione non cambia.

(define (indice-livello img nome)
  (let* ((info (gimp-image-get-layers img)) (n (car info)) (ids (cadr info)))
    (let loop ((i 0))
      (cond ((>= i n) -1)
            ((string=? (car (gimp-item-get-name (vector-ref ids i))) nome) i)
            (else (loop (+ i 1)))))))

(define (id-livello img nome)
  (let* ((info (gimp-image-get-layers img)) (n (car info)) (ids (cadr info)))
    (let loop ((i 0))
      (cond ((>= i n) -1)
            ((string=? (car (gimp-item-get-name (vector-ref ids i))) nome) (vector-ref ids i))
            (else (loop (+ i 1)))))))

; Scarto fra l'angolo del livello di testo e l'inizio effettivo dell'inchiostro:
; misurato ritagliando una copia del livello sul contenuto reale.
(define (scarto-inchiostro img testo)
  (let* ((copia (car (gimp-layer-copy testo FALSE))))
    (gimp-image-insert-layer img copia 0 -1)
    (plug-in-autocrop-layer RUN-NONINTERACTIVE img copia)
    (let ((dx (- (car (gimp-drawable-offsets copia)) (car (gimp-drawable-offsets testo))))
          (dy (- (cadr (gimp-drawable-offsets copia)) (cadr (gimp-drawable-offsets testo)))))
      (gimp-image-remove-layer img copia)
      (list dx dy))))

; Interlinea naturale del font: differenza di altezza fra due righe e una.
(define (interlinea-naturale font dim)
  (let ((una (gimp-text-get-extents-fontname "Ag" dim PIXELS font))
        (due (gimp-text-get-extents-fontname "Ag\nAg" dim PIXELS font)))
    (- (cadr due) (cadr una))))

(define (sostituisci-testo img nome contenuto font dim colore spaziatura interlinea-voluta)
  (let* ((vecchio (id-livello img nome))
         (posto (indice-livello img nome))
         (ox (car (gimp-drawable-offsets vecchio)))
         (oy (cadr (gimp-drawable-offsets vecchio)))
         (nuovo (car (gimp-text-fontname img -1 0 0 contenuto 0 TRUE dim PIXELS font))))
    (gimp-image-remove-layer img vecchio)
    (gimp-text-layer-set-color nuovo colore)
    (gimp-text-layer-set-letter-spacing nuovo spaziatura)
    (if (> interlinea-voluta 0)
        (gimp-text-layer-set-line-spacing nuovo
          (- interlinea-voluta (interlinea-naturale font dim))))
    (gimp-item-set-name nuovo nome)
    (let ((s (scarto-inchiostro img nuovo)))
      (gimp-layer-set-offsets nuovo (- ox (car s)) (- oy (cadr s))))
    (gimp-image-reorder-item img nuovo 0 posto)
    nuovo))

(define (fronte file dpi)
  (let* ((img (car (gimp-file-load RUN-NONINTERACTIVE file file)))
         (pt (/ dpi 72.0))
         (d-nome (* 14 pt))
         (d-ruolo (* 7.5 pt)))
    (sostituisci-testo img "Nome" "CAROLA CASTIGLIONE"
      "Cabinet Grotesk Extrabold" d-nome '(237 232 219) (* 0.12 d-nome) 0)
    ; il punto mediano non puo' stare nel sorgente batch: lo costruisco dal codice carattere
    (sostituisci-testo img "Ruolo"
      (string-append "PRIVATE CHEF " (string (integer->char 183)) " ROMA")
      "Satoshi Medium" d-ruolo '(169 176 160) (* 0.22 d-ruolo) 0)
    (gimp-image-set-active-layer img (id-livello img "Fondo"))
    (gimp-xcf-save RUN-NONINTERACTIVE img (car (gimp-image-get-active-layer img)) file file)
    (gimp-message (string-append "testi modificabili: " file))
    (gimp-image-delete img)))

(define (retro file dpi)
  (let* ((img (car (gimp-file-load RUN-NONINTERACTIVE file file)))
         (pt (/ dpi 72.0))
         (d-claim (* 12 pt))
         (d-cont (* 8.5 pt)))
    (sostituisci-testo img "Claim" "Cucina genuina,\na casa vostra."
      "Cabinet Grotesk Extrabold" d-claim '(27 38 33) 0 (* d-claim 1.22))
    (sostituisci-testo img "Contatti"
      "carola@carolacastiglione.it\n+39 000 000 0000\ncarolacastiglione.it"
      "Satoshi Medium" d-cont '(27 38 33) 0 (* d-cont 1.55))
    (gimp-image-set-active-layer img (id-livello img "Fondo"))
    (gimp-xcf-save RUN-NONINTERACTIVE img (car (gimp-image-get-active-layer img)) file file)
    (gimp-message (string-append "testi modificabili: " file))
    (gimp-image-delete img)))

(fronte "carola-biglietto-fronte.xcf" 300)
(retro  "carola-biglietto-retro.xcf" 300)
(fronte "carola-biglietto-fronte-600dpi.xcf" 600)
(retro  "carola-biglietto-retro-600dpi.xcf" 600)
(gimp-quit 0)
