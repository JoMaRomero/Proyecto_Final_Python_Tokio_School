// Primero esperamos a que el DOM se cargue
document.addEventListener("DOMContentLoaded", function () {
    // Pillamos el tipo que nos indicará si es pelicula o serie
    var tipo = document.getElementById("tipo");

    // Tomamos las ids de los campos que van a ocultarse/mostrarse
    var duration = document.getElementById("duration");
    var numSeasons = document.getElementById("numSeasons");
    var numEpisodes = document.getElementById("numEpisodes");
    var episodeDuration = document.getElementById("episodeDuration");

    // Ocultamos todos los campos hasta recibir el tipo
    duration.style.display = "none";
    numSeasons.style.display = "none";
    numEpisodes.style.display = "none";
    episodeDuration.style.display = "none";

    // Usamos change para hacer el cambio que se escribe en la funcion
    tipo.addEventListener("change", function () {
        // Tomamos el valor del tipo
        var value = this.value;

        // Dependiendo de lo recibido, se muestran y ocultan los bloques
        if (value === "0") { // Si es una película (0) se muestra solo duration
            duration.style.display = "block";
            numSeasons.style.display = "none";
            numEpisodes.style.display = "none";
            episodeDuration.style.display = "none";
        } else if (value === "1") { // Si es una serie (1) se oculta solo duration y los demás se muestran
            duration.style.display = "none";
            numSeasons.style.display = "block";
            numEpisodes.style.display = "block";
            episodeDuration.style.display = "block";
        } else { // Si el valor no es 1 ni 0, se ocultan todos los bloques
            duration.style.display = "none";
            numSeasons.style.display = "none";
            numEpisodes.style.display = "none";
            episodeDuration.style.display = "none";
        }
    });
});
