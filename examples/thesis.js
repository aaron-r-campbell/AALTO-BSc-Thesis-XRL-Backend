colors = [
  "#754C75", // Purple
  "#CC8E00", // Orange
  "#569E56", // Lawn Green
  "#5C8D8D", // Cyan
  "#FF6B6B", // Deep Pink
  "#4C4C75", // Navy
  "#FF1493", // Deep Pink
  "#347448", // Olive
  "#6A438E", // Dark Violet
  "#4C7575", // Teal
  "#4F96CD", // Light Blue
  "#CCA300", // Gold
];

function shuffle(array) {
  // Shuffle the colors array using the Durstenfeld shuffle algorithm
  ret = array.slice();
  for (let i = ret.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ret[i], ret[j]] = [ret[j], ret[i]];
  }
  return ret;
}

function change_colors(array) {
  var r = document.querySelector(":root");
  for (i = 0; i < array.length; i++) {
    r.style.setProperty(`--color${i + 1}`, array[i % array.length]);
  }
}

function fill_list(name, count, content1, content2) {
  try {
    for (i = 0; i < count; i++) {
      document.getElementById(name).innerHTML += `${content1}${i + 1}${content2}`;
    }
  } catch {
    console.log(`${name} not found`);
  }
}

document.addEventListener("keypress", (e) => {
  if (e.key == "Enter") {
    change_colors(shuffle(colors));
  } else if (e.key == "r") {
    change_colors(colors);
  } else {
    try {
      keypress(e);
    } catch {
      console.log("no custom keypress function defined");
    }
  }
});

window.onload = function () {
  try {
    add_elements();
  } catch {
    console.log("no elements to add");
  }

  document.querySelectorAll("*[alt]").forEach((element) => {
    element.style.backgroundImage = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='50%' y='60%' font-size='calc(min(10vw,4em))' text-anchor='middle' fill='%23fff'%3E${element.getAttribute(
      "alt"
    )}%3C/text%3E%3C/svg%3E")`;
  });

  change_colors(colors);
};
