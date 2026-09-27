"""One-off script that writes eval/questions.jsonl. Not part of the pipeline;
kept for the record of how the gold paragraph locations were derived (each
checked against data/parsed/gutenberg/*.json via eval/find.py)."""

import json
from pathlib import Path

QUESTIONS = [
    # Heart of Darkness (219)
    {"id": "hod-01", "source_id": "joseph-conrad_heart-of-darkness", "question": "What does the doctor measure before Marlow leaves for Africa?",
     "answer": "The doctor measures Marlow's skull with calipers.", "gold": [[1, 25]], "type": "factual"},
    {"id": "hod-02", "source_id": "joseph-conrad_heart-of-darkness", "question": "How does Marlow finally manage to secure his position with the Company?",
     "answer": "His aunt uses her personal connections to get him appointed.", "gold": [[1, 18], [1, 26]], "type": "factual"},
    {"id": "hod-03", "source_id": "joseph-conrad_heart-of-darkness", "question": "How is the helmsman killed during the attack on the steamboat?",
     "answer": "He is struck by a spear thrown from the riverbank and dies at Marlow's feet in the pilot-house.", "gold": [[2, 21], [2, 22]], "type": "factual"},
    {"id": "hod-04", "source_id": "joseph-conrad_heart-of-darkness", "question": "What chilling phrase does Kurtz scrawl at the end of his otherwise eloquent report?",
     "answer": "\"Exterminate all the brutes!\"", "gold": [[2, 28]], "type": "factual"},
    {"id": "hod-05", "source_id": "joseph-conrad_heart-of-darkness", "question": "What decorates the posts around Kurtz's house at the Inner Station?",
     "answer": "Shrunken human heads mounted on stakes.", "gold": [[3, 4], [3, 5]], "type": "factual"},
    {"id": "hod-06", "source_id": "joseph-conrad_heart-of-darkness", "question": "Who does the brickmaker describe as 'the chief of the Inner Station'?",
     "answer": "Mr. Kurtz.", "gold": [[1, 58]], "type": "named_entity"},
    {"id": "hod-07", "source_id": "joseph-conrad_heart-of-darkness", "question": "Which Company employee does Marlow admire for keeping immaculate books and dress amid the chaos of the station?",
     "answer": "The Company's chief accountant.", "gold": [[1, 42]], "type": "named_entity"},
    {"id": "hod-08", "source_id": "joseph-conrad_heart-of-darkness", "question": "What does Marlow nickname the young Russian sailor who reveres Kurtz and wears patched, multicolored clothing?",
     "answer": "The harlequin.", "gold": [[3, 0]], "type": "named_entity"},
    {"id": "hod-09", "source_id": "joseph-conrad_heart-of-darkness", "question": "What makes the Company's headquarters in Europe feel unsettling to Marlow before he even departs?",
     "answer": "A dead, deserted street and two old women silently knitting black wool by the entrance give the office a death-haunted, unsettling atmosphere.", "gold": [[1, 21], [1, 23]], "type": "paraphrase"},
    {"id": "hod-10", "source_id": "joseph-conrad_heart-of-darkness", "question": "What convinces Marlow that the local workers at the first station are being treated as expendable?",
     "answer": "He finds African laborers abandoned in the shade near a grove, starving and dying from overwork and disease, discarded once no longer useful.", "gold": [[1, 39]], "type": "paraphrase"},
    {"id": "hod-11", "source_id": "joseph-conrad_heart-of-darkness", "question": "How does the Company's early praise of Kurtz compare with what Marlow actually discovers at his station?",
     "answer": "Kurtz is praised as a remarkable agent and 'chief of the Inner Station,' but Marlow finds his house surrounded by shrunken human heads on stakes.", "gold": [[1, 58], [3, 4], [3, 5]], "type": "multi_hop"},
    {"id": "hod-12", "source_id": "joseph-conrad_heart-of-darkness", "question": "How does the doctor's remark about mental changes in colonial agents foreshadow what happens to Kurtz?",
     "answer": "The doctor predicts that isolation in the tropics causes mental changes in those who go out there; Kurtz's descent into savagery and his final cry 'The horror! The horror!' fulfill that prediction.", "gold": [[1, 25], [3, 42]], "type": "multi_hop"},
    {"id": "hod-13", "source_id": "joseph-conrad_heart-of-darkness", "question": "How does Marlow's view of Kurtz evolve from rumor to direct encounter to aftermath?",
     "answer": "He hears Kurtz praised as an exceptional agent, then witnesses the brutality and heads on stakes at his station, hears his dying words 'The horror! The horror!', and afterward protects his memory by lying to his Intended.", "gold": [[1, 58], [2, 28], [3, 4], [3, 5], [3, 42]], "type": "thematic"},
    {"id": "hod-14", "source_id": "joseph-conrad_heart-of-darkness", "question": "What is the name of Marlow's wife?",
     "answer": "Not stated — the book never mentions Marlow having a wife.", "gold": [], "type": "not_in_book"},
    {"id": "hod-15", "source_id": "joseph-conrad_heart-of-darkness", "question": "What is Kurtz's first name?",
     "answer": "Not given — he is referred to only as 'Mr. Kurtz' throughout.", "gold": [], "type": "not_in_book"},

    # Pride and Prejudice (1342)
    {"id": "pp-01", "source_id": "jane-austen_pride-and-prejudice", "question": "According to the novel's opening line, what must a single man in possession of a good fortune be in want of?",
     "answer": "A wife.", "gold": [[1, 0]], "type": "factual"},
    {"id": "pp-02", "source_id": "jane-austen_pride-and-prejudice", "question": "Why is the Bennet family estate entailed away from Mr. Bennet's daughters?",
     "answer": "Because he has no son, the estate passes to the nearest male relative, Mr. Collins, instead of his daughters.", "gold": [[7, 0]], "type": "factual"},
    {"id": "pp-03", "source_id": "jane-austen_pride-and-prejudice", "question": "Who does Charlotte Lucas marry despite having no real affection for him?",
     "answer": "Mr. Collins.", "gold": [[22, 1]], "type": "factual"},
    {"id": "pp-04", "source_id": "jane-austen_pride-and-prejudice", "question": "What does Lady Catherine de Bourgh demand Elizabeth promise her regarding Darcy?",
     "answer": "That Elizabeth will never enter into an engagement with him.", "gold": [[56, 46], [56, 66]], "type": "factual"},
    {"id": "pp-05", "source_id": "jane-austen_pride-and-prejudice", "question": "Who does Lydia run off with, causing a family scandal?",
     "answer": "Mr. Wickham.", "gold": [[46, 4]], "type": "factual"},
    {"id": "pp-06", "source_id": "jane-austen_pride-and-prejudice", "question": "Who proposes to Elizabeth in Chapter 19, citing his duty as a clergyman and Lady Catherine's advice as his reasons for marrying?",
     "answer": "Mr. Collins.", "gold": [[19, 7]], "type": "named_entity"},
    {"id": "pp-07", "source_id": "jane-austen_pride-and-prejudice", "question": "Who is the housekeeper at Pemberley who praises Darcy as 'the best landlord, and the best master'?",
     "answer": "Mrs. Reynolds.", "gold": [[43, 37]], "type": "named_entity"},
    {"id": "pp-08", "source_id": "jane-austen_pride-and-prejudice", "question": "Why does Elizabeth initially believe Darcy treated Wickham unfairly?",
     "answer": "Wickham tells her that Darcy's late father promised him a valuable church position, which Darcy denied him out of jealousy.", "gold": [[16, 24], [16, 26]], "type": "paraphrase"},
    {"id": "pp-09", "source_id": "jane-austen_pride-and-prejudice", "question": "What makes Elizabeth begin to doubt her harsh judgment of Darcy after their argument at Hunsford?",
     "answer": "His letter gives a detailed counter-account of the Wickham affair and his role in separating Jane and Bingley, which makes her question what she'd believed.", "gold": [[35, 4]], "type": "paraphrase"},
    {"id": "pp-10", "source_id": "jane-austen_pride-and-prejudice", "question": "How does Wickham's account of being denied a promised position compare with Darcy's own explanation in his letter?",
     "answer": "Wickham claims Darcy's father bequeathed him a living that Darcy refused to honor; Darcy's letter says Wickham was given money in place of the living, squandered it, and later tried to elope with Darcy's sister.", "gold": [[16, 24], [16, 26], [35, 4]], "type": "multi_hop"},
    {"id": "pp-11", "source_id": "jane-austen_pride-and-prejudice", "question": "How does the housekeeper's opinion of Darcy at Pemberley compare with Elizabeth's opinion of him right after his first proposal?",
     "answer": "Right after his proposal, Elizabeth considers him arrogant and resentful; Mrs. Reynolds instead describes him as the kindest, most generous master and landlord she has known.", "gold": [[34, 8], [43, 37]], "type": "multi_hop"},
    {"id": "pp-12", "source_id": "jane-austen_pride-and-prejudice", "question": "How does Elizabeth's opinion of Darcy shift over the course of the novel?",
     "answer": "She goes from disliking him as proud and unfeeling, to rejecting his first proposal in anger, to being persuaded by his letter and Pemberley's household that she misjudged him, and finally to loving him.", "gold": [[34, 3], [34, 8], [35, 4], [43, 37]], "type": "thematic"},
    {"id": "pp-13", "source_id": "jane-austen_pride-and-prejudice", "question": "How does the family's financial situation shape the pressure on the Bennet daughters to marry well?",
     "answer": "Because the estate is entailed to Mr. Collins and the daughters have little fortune, marrying well is presented as almost a necessity for their future security.", "gold": [[7, 0], [1, 0]], "type": "thematic"},
    {"id": "pp-14", "source_id": "jane-austen_pride-and-prejudice", "question": "Where do Elizabeth and Darcy go on their honeymoon?",
     "answer": "Not stated — the novel ends shortly after the wedding without describing a honeymoon.", "gold": [], "type": "not_in_book"},
    {"id": "pp-15", "source_id": "jane-austen_pride-and-prejudice", "question": "What are the names of Elizabeth and Darcy's children?",
     "answer": "Not stated — the novel doesn't extend into their married life.", "gold": [], "type": "not_in_book"},

    # The Adventures of Sherlock Holmes (1661)
    {"id": "sh-01", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What title does Holmes always use when he refers to Irene Adler?",
     "answer": "He calls her 'the woman.'", "gold": [[1, 0]], "type": "factual"},
    {"id": "sh-02", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What kind of snake kills Dr. Roylott?",
     "answer": "A swamp adder.", "gold": [[8, 244]], "type": "factual"},
    {"id": "sh-03", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Who confesses to hiding the blue carbuncle inside the Christmas goose?",
     "answer": "James Ryder.", "gold": [[7, 168]], "type": "factual"},
    {"id": "sh-04", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What organization is signified by the letters found on the orange pips sent as warnings?",
     "answer": "The Ku Klux Klan (K.K.K.).", "gold": [[5, 51]], "type": "factual"},
    {"id": "sh-05", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What had the Red-Headed League actually been digging under the pawnbroker's shop?",
     "answer": "A tunnel toward the neighboring bank's vault.", "gold": [[2, 210]], "type": "factual"},
    {"id": "sh-06", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Who is unmasked as the mysterious suitor 'Hosmer Angel'?",
     "answer": "Mary Sutherland's stepfather, Mr. Windibank.", "gold": [[3, 127]], "type": "named_entity"},
    {"id": "sh-07", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Who is revealed to be the disfigured beggar 'Hugh Boone'?",
     "answer": "Neville St. Clair.", "gold": [[6, 74]], "type": "named_entity"},
    {"id": "sh-08", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Who does Holmes conclude is the real prisoner hidden away at the Copper Beeches?",
     "answer": "Alice Rucastle.", "gold": [[12, 169]], "type": "named_entity"},
    {"id": "sh-09", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Who does Mr. Holder identify as a bad influence on his son Arthur, connected to the missing beryl gems?",
     "answer": "Sir George Burnwell.", "gold": [[11, 38], [11, 39]], "type": "named_entity"},
    {"id": "sh-10", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Why does Holmes rank his opinion of one particular woman above all other women he's outwitted?",
     "answer": "Because she, Irene Adler, is the one person whose cleverness actually got the better of him.", "gold": [[1, 258]], "type": "paraphrase"},
    {"id": "sh-11", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "Why does the pawnbroker's assistant push to spend unpaid hours working in the cellar?",
     "answer": "He's secretly using the time to dig a tunnel toward the neighboring bank's gold.", "gold": [[2, 210]], "type": "paraphrase"},
    {"id": "sh-12", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "How does the reveal of Hugh Boone's true identity compare to the reveal of Hosmer Angel's true identity?",
     "answer": "Both are deceptions by someone close to the victim: Neville St. Clair posed as the beggar Hugh Boone to secretly earn money, while Mary Sutherland's own stepfather posed as suitor Hosmer Angel to keep her from marrying and losing her income.", "gold": [[6, 74], [3, 127]], "type": "multi_hop"},
    {"id": "sh-13", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "How do the schemes in 'The Red-Headed League' and 'A Case of Identity' both use a fabricated identity to manipulate their victim?",
     "answer": "In both, the con artist invents a false persona or scheme (Vincent Spaulding's tunneling disguised as a red-headed men's league; Mr. Windibank's Hosmer Angel disguise) to control the victim's actions without raising suspicion.", "gold": [[2, 35], [3, 127]], "type": "multi_hop"},
    {"id": "sh-14", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What principle does Holmes state about the danger of forming theories before gathering evidence?",
     "answer": "That it is a capital mistake to theorize before you have data, because it biases you toward twisting facts to fit theories instead of theories to fit facts.", "gold": [[1, 23]], "type": "thematic"},
    {"id": "sh-15", "source_id": "arthur-conan-doyle_the-adventures-of-sherlock-holmes", "question": "What university did Sherlock Holmes attend?",
     "answer": "Not stated in these stories.", "gold": [], "type": "not_in_book"},
]


def main() -> None:
    out = Path("eval/questions.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for q in QUESTIONS:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"wrote {len(QUESTIONS)} questions to {out}")


if __name__ == "__main__":
    main()
