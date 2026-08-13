; Sostituisce il livello Monogramma con la versione renderizzata dall'SVG
; e aggiunge nel file il tracciato vettoriale, modificabile e scalabile.

(define (indice-livello img nome)
  (let* ((info (gimp-image-get-layers img))
         (n (car info))
         (ids (cadr info)))
    (let loop ((i 0))
      (cond ((>= i n) -1)
            ((string=? (car (gimp-item-get-name (vector-ref ids i))) nome) i)
            (else (loop (+ i 1)))))))

(define (id-livello img nome)
  (let* ((info (gimp-image-get-layers img))
         (n (car info))
         (ids (cadr info)))
    (let loop ((i 0))
      (cond ((>= i n) -1)
            ((string=? (car (gimp-item-get-name (vector-ref ids i))) nome) (vector-ref ids i))
            (else (loop (+ i 1)))))))

(define (lavora psd svg D x y base dpi)
  (let* ((img (car (gimp-file-load RUN-NONINTERACTIVE psd psd)))
         (posto (indice-livello img "Monogramma"))
         (vecchio (id-livello img "Monogramma"))
         (svgimg (car (file-svg-load RUN-NONINTERACTIVE svg svg dpi D D 0)))
         (svglayer (vector-ref (cadr (gimp-image-get-layers svgimg)) 0))
         (nuovo (car (gimp-layer-new-from-drawable svglayer img))))

    ; monogramma: pixel generati dal vettore, al posto della vecchia versione
    (gimp-image-remove-layer img vecchio)
    (gimp-image-insert-layer img nuovo 0 posto)
    (gimp-item-set-name nuovo "Monogramma")
    (gimp-layer-set-offsets nuovo x y)
    (gimp-image-delete svgimg)

    ; tracciato vettoriale unico (merge), scalabile senza perdita di qualita'
    (let* ((vec (vector-ref (cadr (gimp-vectors-import-from-file img svg TRUE FALSE)) 0))
           (m (/ D 100.0)))
      (gimp-item-set-name vec "Monogramma (tracciato vettoriale)")
      (gimp-item-transform-scale vec
        (+ x (* 6 m)) (+ y (* 6 m))
        (+ x (* 94 m)) (+ y (* 94 m)))
      (gimp-item-set-visible vec FALSE))

    (gimp-image-set-resolution img dpi dpi)
    (gimp-image-set-active-layer img (id-livello img "Fondo"))

    (gimp-xcf-save RUN-NONINTERACTIVE img (car (gimp-image-get-active-layer img))
                   (string-append base ".xcf") (string-append base ".xcf"))
    (file-psd-save RUN-NONINTERACTIVE img (car (gimp-image-get-active-layer img))
                   psd psd 1 0)
    (gimp-message (string-append "salvato " base ".psd e .xcf"))
    (gimp-image-delete img)))

; monogramma sciolto ad alta risoluzione, fondo trasparente
(define (esporta-png svg out lato)
  (let* ((img (car (file-svg-load RUN-NONINTERACTIVE svg svg 300 lato lato 0)))
         (lay (vector-ref (cadr (gimp-image-get-layers img)) 0)))
    (file-png-save RUN-NONINTERACTIVE img lay out out 0 9 1 1 1 1 1)
    (gimp-message (string-append "salvato " out))
    (gimp-image-delete img)))

(lavora "carola-biglietto-fronte.psd" "monogramma-cc-scuro.svg" 170 452 185 "carola-biglietto-fronte" 300)
(lavora "carola-biglietto-retro.psd" "monogramma-cc-chiaro.svg" 104 835 191 "carola-biglietto-retro" 300)
(esporta-png "monogramma-cc-scuro.svg"  "monogramma-cc-scuro-2400.png"  2400)
(esporta-png "monogramma-cc-chiaro.svg" "monogramma-cc-chiaro-2400.png" 2400)
(gimp-quit 0)
