---
title: 'Jedna oferta. 349 320 zł przy budżecie 350 000 zł.'
lead: 'Postępowanie na integrację systemu szpitalnego z Centralną e-Rejestracją, które śledziliśmy od sierpnia, zakończyło się jedną ofertą. Odpowiedź zamawiającego na pytanie o dokumentację interfejsów wyjaśnia dlaczego.'
date: 2026-10-21T08:30:00+02:00
draft: false
authors:
  - sylwester-cyrwus
category: procedures
cover: jedna-oferta.jpg
coverAlt: 'Grafika satyryczna wygenerowana przez AI. Zmyślony dostawca HIS ze złotym kluczem na smyczy śmieje się obok lekarza, którego ekran blokuje czerwona kłódka.'
coverCaption: 'Grafika satyryczna wygenerowana przez AI. Postać dostawcy HIS jest zmyślona i nie przedstawia żadnej firmy ani osoby.'
translationKey: jedna-oferta
sources:
  - 'Postępowanie ZP-1559-2026: specyfikacja warunków zamówienia, wyjaśnienia treści SWZ z 22 września 2026 oraz informacja o wyborze oferty z 19 października 2026 (dokumenty publiczne postępowania).'
  - 'Ogłoszenie o zamówieniu w Dzienniku Urzędowym Unii Europejskiej, numer 2026/S 167-597514.'
  - 'Centrum e-Zdrowia, konsultacje projektu otwartych standardów komunikacji między systemami (art. 8d), termin zgłaszania uwag 31 października 2026.'
  - 'HL7 FHIR, zasób CapabilityStatement: https://hl7.org/fhir/capabilitystatement.html'
---

*Pierwszy odcinek serii „Jedna oferta”, opublikowany 21 października 2026 na LinkedIn. Tekst w wersji z tamtego dnia, ze śródtytułami i wykazem dokumentów.*

Jedna oferta. 349 320 zł przy budżecie 350 000 zł. Tak 19 października rozstrzygnięto postępowanie, które śledziłem od sierpnia, bo zadawaliśmy w nim pytania. Oferty nie złożyliśmy. Zaraz wyjaśnię dlaczego.

## Co kupował szpital

Przedmiot: integracja systemu szpitalnego z Centralną e-Rejestracją. Szpital wojewódzki, pieniądze unijne. We wrześniu, po naszych pytaniach, zamawiający dopuścił moduł równoważny, opisał sześć kryteriów równoważności, obniżył próg udziału z 400 do 200 tys. zł i przedłużył termin. Podręcznikowo.

## Pytanie o dokumentację interfejsów

Potem zapytaliśmy o jedno: kto udostępni dokumentację interfejsów systemu, z którym mamy się zintegrować. Odpowiedź z 22 września, cytuję:

> „Zamawiający nie posiada dokumentacji technicznej interfejsów systemu HIS (…) i nie ma możliwości jej pozyskania ani udostępnienia wykonawcom, ponieważ dokumentacja ta stanowi dokumentację własnościową producenta systemu”.

Szpital nie ma dokumentacji interfejsów własnego systemu. I nie ma możliwości jej dostać.

## Kto płaci za zgodę producenta

Dalej: koszty „zgód, udostępnienia interfejsów lub usług producenta HIS” wykonawca ma „uwzględnić w cenie oferty”. A przed złożeniem oferty zamawiający „zaleca dokonanie niezbędnych ustaleń z producentem systemu HIS”.

Czyli o tym, kto może konkurować, decyduje producent. A cenę jego zgody i tak zapłaci szpital, w cenie jedynej oferty.

Nie składa się oferty na coś, czego nie da się wycenić. Złożył ją jeden podmiot.

## To samo pytanie w większej skali

Dziś to samo pytanie wraca w większej skali. Do 31 października Centrum e-Zdrowia zbiera uwagi do projektu otwartych standardów komunikacji między systemami. Projekt ureguluje format danych: 30 profili na HL7 FHIR. Nie ureguluje tego, co rozstrzygnęło to postępowanie: czy szpital ma prawo do opisu interfejsów swojego systemu i czy może go dać wykonawcy, którego sam wybrał.

## Trzy zdania do każdej umowy

Trzy zdania, których szukałbym w każdej umowie z producentem systemu szpitalnego:

1. Opis interfejsów instalacji jest w posiadaniu szpitala i szpital może go przekazać wykonawcy, którego wskaże.
2. Warunki i cena dostępu strony trzeciej do interfejsów są ustalone w dniu podpisania umowy, nie przy każdej integracji od nowa.
3. Szpital decyduje, kto dostaje dostęp do środowiska testowego jego systemu.

Czy jest szansa, żeby pierwsze z nich stało się obowiązkiem? Publiczny opis możliwości każdej instalacji? W FHIR ten mechanizm już istnieje i nazywa się CapabilityStatement.

Dyrektorzy, szefowie IT: które z tych trzech zdań macie w swojej umowie? Jeśli żadnego, to nie Wasza wina. Nikt tego od Was nie wymagał. Ale teraz wiecie, jak wygląda przetarg bez nich.
