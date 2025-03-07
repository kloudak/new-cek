function getElementHeightWithMargin(elem) {
  // Get the element's computed style
  const style = window.getComputedStyle(elem);

  // Get element's offsetHeight
  const height = elem.offsetHeight;

  // Get margins (convert them to integer values)
  const marginTop = parseInt(style.marginTop, 10);
  const marginBottom = parseInt(style.marginBottom, 10);

  // Total height calculation including margins
  return height + marginTop + marginBottom;
}

function getIntersection(list1, list2) {
  const set2 = new Set(list2);
  return list1.filter((item) => set2.has(item));
}

// Function to highlight searched text
function highlightText(term, container) {
  if (container) {
    let regex = new RegExp("(" + term + ")", "gi");

    // Function to walk through all text nodes within the container
    function walkAndHighlight(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        let match = regex.exec(node.nodeValue);
        if (match) {
          // Split the text node and insert highlight span
          let highlightSpan = document.createElement("span");
          highlightSpan.className = "highlight";
          highlightSpan.textContent = match[0];

          let afterMatch = node.splitText(match.index);
          afterMatch.nodeValue = afterMatch.nodeValue.substring(match[0].length);

          node.parentNode.insertBefore(highlightSpan, afterMatch);
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        // Recursively call for each child node
        for (let i = 0; i < node.childNodes.length; i++) {
          walkAndHighlight(node.childNodes[i]);
        }
      }
    }

    walkAndHighlight(container);
  }
}

// Function to remove all highlights (removes all span.highlight elements)
function remove_highlight() {
  // Find all span elements with the class 'highlight'
  let highlightedSpans = document.querySelectorAll("span.highlight");

  // Loop through each highlighted span and unwrap it (replace with its inner content)
  highlightedSpans.forEach(function (span) {
    let parent = span.parentNode;
    while (span.firstChild) {
      parent.insertBefore(span.firstChild, span);
    }
    parent.removeChild(span);
  });

  // Get the current domain (localhost or production)
  const currentDomain = window.location.origin;

  // Send an AJAX request to cancel the search
  fetch(`${currentDomain}/cancel-search/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// Function to get the CSRF token from the cookies (needed for Django POST requests)
function getCSRFToken() {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    let cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.startsWith("csrftoken=")) {
        cookieValue = cookie.substring("csrftoken=".length, cookie.length);
        break;
      }
    }
  }
  return cookieValue;
}

dataTableCS = {
  emptyTable: "Tabulka neobsahuje žádná data",
  info: "Zobrazuji _START_ až _END_ z celkem _TOTAL_ záznamů",
  infoEmpty: "Zobrazuji 0 až 0 z 0 záznamů",
  infoFiltered: "(filtrováno z celkem _MAX_ záznamů)",
  loadingRecords: "Načítám...",
  zeroRecords: "Žádné záznamy nebyly nalezeny",
  paginate: {
    first: "První",
    last: "Poslední",
    next: "Další",
    previous: "Předchozí",
  },
  searchBuilder: {
    add: "Přidat podmínku",
    clearAll: "Smazat vše",
    condition: "Podmínka",
    conditions: {
      date: {
        after: "po",
        before: "před",
        between: "mezi",
        empty: "prázdné",
        equals: "rovno",
        not: "není",
        notBetween: "není mezi",
        notEmpty: "není prázdné",
      },
      number: {
        between: "mezi",
        empty: "prázdné",
        equals: "rovno",
        gt: "větší",
        gte: "rovno a větší",
        lt: "menší",
        lte: "rovno a menší",
        not: "není",
        notBetween: "není mezi",
        notEmpty: "není prázdné",
      },
      string: {
        contains: "obsahuje",
        empty: "prázdné",
        endsWith: "končí na",
        equals: "rovno",
        not: "není",
        notEmpty: "není prázdné",
        startsWith: "začíná na",
        notContains: "Podmínka",
        notStartsWith: "Nezačíná",
        notEndsWith: "Nekončí",
      },
      array: {
        equals: "rovno",
        empty: "prázdné",
        contains: "obsahuje",
        not: "není",
        notEmpty: "není prázdné",
        without: "neobsahuje",
      },
    },
    data: "Sloupec",
    logicAnd: "A",
    logicOr: "NEBO",
    title: {
      0: "Rozšířený filtr",
      _: "Rozšířený filtr (%d)",
    },
    value: "Hodnota",
    button: {
      0: "Rozšířený filtr",
      _: "Rozšířený filtr (%d)",
    },
    deleteTitle: "Smazat filtrovací pravidlo",
    leftTitle: "Zrušení odsazení podmínky",
    rightTitle: "Odsazení podmínky",
  },
  autoFill: {
    cancel: "Zrušit",
    fill: "Vyplň všechny buňky textem <i>%d<i></i></i>",
    fillHorizontal: "Vyplň všechny buňky horizontálně",
    fillVertical: "Vyplň všechny buňky vertikálně",
    info: "Příklad automatického vyplňování",
  },
  buttons: {
    collection:
      'Kolekce <span class="ui-button-icon-primary ui-icon ui-icon-triangle-1-s"></span>',
    copy: "Kopírovat",
    copyTitle: "Kopírovat do schránky",
    csv: "CSV",
    excel: "Excel",
    pageLength: {
      "-1": "Zobrazit všechny řádky",
      _: "Zobrazit %d řádků",
      1: "Zobraz 1 řádek",
    },
    pdf: "PDF",
    print: "Tisknout",
    colvis: "Viditelnost sloupců",
    colvisRestore: "Resetovat sloupce",
    copyKeys:
      "Zmáčkněte ctrl or u2318 + C pro zkopírování dat.  Pro zrušení klikněte na tuto zprávu nebo zmáčkněte esc..",
    copySuccess: {
      1: "Zkopírován 1 řádek do schránky",
      _: "Zkopírováno %d řádků do schránky",
    },
    createState: "Vytvořit Stav",
    removeAllStates: "Vymazat všechny Stavy",
    removeState: "Odstranit",
    renameState: "Odstranit",
    savedStates: "Uložit Stavy",
    stateRestore: "Stav %d",
    updateState: "Aktualizovat",
  },
  searchPanes: {
    clearMessage: "Smazat vše",
    collapse: {
      0: "Vyhledávací Panely",
      _: "Vyhledávací Panely (%d)",
    },
    count: "{total}",
    countFiltered: "{shown} ({total})",
    emptyPanes: "Žádné Vyhledávací Panely",
    loadMessage: "Načítám Vyhledávací Panely",
    title: "Aktivních filtrů - %d",
    showMessage: "Zobrazit Vše",
    collapseMessage: "Sbalit Vše",
  },
  select: {
    cells: {
      1: "Vybrán 1 záznam",
      _: "Vybráno %d záznamů",
    },
    columns: {
      1: "Vybrán 1 sloupec",
      _: "Vybráno %d sloupců",
    },
    rows: {
      1: "Vybrán 1 řádek",
      _: "Vybráno %d řádků",
    },
  },
  aria: {
    sortAscending: "Aktivujte pro seřazení vzestupně",
    sortDescending: "Aktivujte pro seřazení sestupně",
  },
  lengthMenu: "Zobrazit _MENU_ výsledků",
  processing: "Zpracovávání...",
  search: "Vyhledávání:",
  datetime: {
    previous: "Předchozí",
    next: "Další",
    hours: "Hodiny",
    minutes: "Minuty",
    seconds: "Vteřiny",
    unknown: "-",
    amPm: ["Dopoledne", "Odpoledne"],
    weekdays: ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"],
    months: [
      "Leden",
      "Únor",
      "Březen",
      "Duben",
      "Květen",
      "Červen",
      "Červenec",
      "Srpen",
      "Září",
      "Říjen",
      "Listopad",
      "Prosinec",
    ],
  },
  editor: {
    close: "Zavřít",
    create: {
      button: "Nový",
      title: "Nový záznam",
      submit: "Vytvořit",
    },
    edit: {
      button: "Změnit",
      title: "Změnit záznam",
      submit: "Aktualizovat",
    },
    remove: {
      button: "Vymazat",
      title: "Smazání",
      submit: "Vymazat",
      confirm: {
        _: "Opravdu chcete smazat tyto %d řádky?",
        1: "Opravdu chcete smazat tento 1 řádek?",
      },
    },
    multi: {
      title: "Mnohočetný výběr",
      restore: "Vrátit změny",
      noMulti:
        "Toto pole může být editováno individuálně, ale ne jako soušást skupiny.",
      info: "Vybrané položky obsahují různé hodnoty pro tento vstup. Chcete-li upravit a nastavit všechny položky tohoto vstupu na stejnou hodnotu, klikněte nebo klepněte sem, jinak si zachovají své individuální hodnoty.",
    },
    error: {
      system:
        'Došlo k systémové chybě (&lt;a target="\\" rel="nofollow" href="\\"&gt;Více informací&lt;/a&gt;).',
    },
  },
  infoThousands: " ",
  decimal: ",",
  thousands: " ",
  stateRestore: {
    creationModal: {
      button: "Vytvořit",
      columns: {
        search: "Vyhledávání v buňce",
        visible: "Viditelnost buňky",
      },
      name: "Název:",
      order: "Řazení",
      paging: "Stránkování",
      scroller: "Pozice skrolování",
      select: "Výběr",
      title: "Vytvořit nový Stav",
      toggleLabel: "Zahrnout",
      search: "Filtrování",
      searchBuilder: "Rozšířené filtrování",
    },
    duplicateError: "Stav s tímto názvem ji existuje.",
    emptyError: "Název nemůže být prázný.",
    emptyStates: "Žádné uložené stavy",
    removeConfirm: "Opravdu chcete odstranbit %s?",
    removeError: "Chyba při odstraňování stavu.",
    removeJoiner: "a",
    removeSubmit: "Odstranit",
    removeTitle: "Odstranit Stav",
    renameButton: "Vymazat",
    renameLabel: "Nové jméno pro %s:",
    renameTitle: "Přejmenování Stavu",
  },
  searchPlaceholder: "",
};

$(document).ready(function () {
  const modal = document.getElementById("modal-video");
  const closeModalBtn = document.getElementById("close-modal");

  const openModalButtons = document.querySelectorAll(".open-modal-video");

  // Add event listener to each button to open the modal
  openModalButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      const videoId = button.getAttribute("data-video");
      document.querySelectorAll("#modal-video iframe").forEach((iframe) => {
        iframe.style.display = "none";
      });
      document.getElementById(videoId).style.display = "block";
      modal.showModal();
    });
  });

  // Function to stop the video
  function stopVideo() {
    document.querySelectorAll("#modal-video iframe").forEach((iframe) => {
      const videoSrc = iframe.src;
      if (videoSrc !== "") {
        iframe.src = "";
        iframe.src = videoSrc;
      }
    });
  }
  // Close the modal when the "Zavřít" button is clicked
  closeModalBtn.addEventListener("click", function () {
    stopVideo();
    modal.close();
  });

  // Close the modal when pressing the ESC key
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && modal.open) {
      stopVideo();
      modal.close();
    }
  });

  // Detect when input is cleared
  document.getElementById('search-input').addEventListener('input', function(event) {
    if (event.target.value === '') {
        remove_highlight();
    }
});
});
