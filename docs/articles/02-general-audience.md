# The Stick That Was Split in Two

### A very old idea about trust, and what it can teach us about AI assistants

---

Imagine you send someone to the market for you.

You tell them: buy bread, buy milk, buy eggs. They come back with bread, milk, eggs - and you say, "Why did you buy a chicken? I never told you to buy a chicken."

They say they didn't buy a chicken.

Now what? You remember one thing. They remember another. One of you is wrong, and there is no way to tell who.

This is a very old problem. It is also, right now, one of the most urgent unsolved problems in how we build AI assistants - because we are handing them our credit cards, our calendars and our email accounts, and telling them to go do things on our behalf.

---

## How people solved it in the Middle Ages

Before paper records were common, there was a clever tool for this. It was called a **tally stick**.

Here's how it worked. You take a stick of wood. You carve notches into it - one notch for each unit of whatever you're agreeing on. Then you **split the stick down the middle, lengthwise.**

You keep one half. The other person keeps the other half.

The beauty is in the wood grain. Every stick splits along a unique, jagged, impossible-to-fake line. When you put the two halves back together, they either match perfectly or they don't. Neither half means anything alone. Neither person can add a notch later without it becoming obvious when the halves are rejoined.

Nobody has to be trusted. The stick does the remembering.

That's where the name of this project comes from. I wanted to know: could something like a tally stick work for AI assistants? And if not, why not?

---

## What most AI assistants do today

Here's the uncomfortable part.

Most systems that let an AI act on your behalf work roughly like this: you give the assistant a permission slip, and the assistant keeps its own diary of what it did.

Think about that for a moment. If there's ever a disagreement, the only record is **the diary kept by the party being accused.**

That's not a tally stick. That's one person's word.

I built a testing setup to measure how bad this actually is. I generated thousands of imaginary disagreements - some where the assistant genuinely misbehaved, some where the person misremembered, some where somebody was lying outright - and ran a range of different record-keeping schemes against them to see which disagreements each could actually settle.

The permission-slip-and-diary approach, which is what most real systems use, settled **none** of the cases where the *person* was the one in the wrong. Zero out of a hundred.

A tally-stick style approach - where both sides hold matching halves of the agreement - settled **all** of them. A hundred out of a hundred.

So far, so encouraging.

---

## The lie that no stick can catch

Then I found the thing that ruined it, and it turned out to be the interesting part.

The tally stick works beautifully when someone **says something false**. You claimed you only asked for two things? Here's the stick, and it has three notches. Done. The stick wins.

But what about someone who doesn't say anything false at all?

Picture this. The assistant is asked to produce its half of the stick. It says:

> "I lost it."

That's not a lie you can catch with a stick. There's no notch that contradicts it. And here's the genuinely difficult thing:

**Someone who lost their half by accident says exactly the same words as someone who threw theirs in the fire.**

I tested this carefully. I built pairs of scenarios that were identical in every visible detail - the honest one and the dishonest one - differing only in what was actually true underneath. Then I checked whether any scheme could tell them apart.

None could. Not one.

---

## "So just punish anyone who can't produce it"

That's the obvious fix, and I tried it. You make a rule: if you can't produce your half, you lose.

It works. All the cheaters who claimed they lost the stick are now caught.

And so is every single honest person who really did lose it.

I measured the trade exactly, and it was chillingly neat: **for every cheater the rule caught, it wrongly condemned exactly one honest person.** Not roughly one. Exactly one. The total amount of unfairness in the system didn't budge - it just moved.

Which gives the sentence I'd most want someone to take away from all this:

> **Forcing people to answer doesn't create justice. It changes who suffers the injustice.**

Before the rule, the person who got hurt was the victim of a cheater who got away with it. After the rule, the person who got hurt is the honest one who genuinely had bad luck.

There is no cleverness that avoids this. It isn't a flaw in the design. It's a property of the situation: "I can't produce it" is a single signal, and both the honest and the dishonest world produce it. One signal cannot carry two meanings.

---

## The one distinction that actually matters

Digging into why, I found a line that divides the cases cleanly, and once you see it you can't unsee it.

Compare two situations.

**Situation one.** You said you only authorised two things. The stick shows three. Maybe you're lying. Maybe you honestly forgot. Either way - **your account and the record disagree.**

**Situation two.** The assistant can't produce its half. Maybe it burned it. Maybe it lost it. In the burning case something dishonest happened. In the losing case **nothing disagrees with anything.** There's just a gap.

Here's the difference that matters:

In situation one, there is a true thing you can say about *both* possibilities at once: *"your account doesn't match the record."* That's true whether you lied or forgot. So you can be fair to both by saying that and stopping - by talking about **the record** instead of about **the person**.

In situation two, there is nothing true you can say about both. Either something was hidden or it wasn't, and you cannot know which.

So:

> **When two situations differ only in *why* something happened, you can be fair to both.**
> **When they differ in *whether* it happened at all, you cannot.**

The practical upshot is smaller than it sounds but genuinely useful: systems should say *"these two accounts don't match"* rather than *"this person is at fault."* The first is provable. The second usually isn't - and in my tests, systems that insisted on naming a culprit ended up blaming people who had simply misremembered, over and over.

---

## The part that surprised me most

I'll be honest: I started this hoping to invent something.

I didn't. Everything I "discovered" about how to protect a falsely-accused party had already been worked out by researchers between 1996 and 2010. There's a paper from 2007 with a theorem that says, near enough, exactly what I'd been circling for weeks.

Fine - that happens in research. But then I checked whether the people currently building AI agent systems were citing that work.

**They aren't. None of it. Not one of the four separate research lines that solved this.**

They're doing good work. But they're all solving the *owner's* problem: proving the assistant had permission. Almost nobody is solving the *assistant's* problem: proving it didn't do the thing it's accused of.

And the old answers are sitting right there, thirty years old, uncited.

That's not a clever finding. It required no experiments at all - just reading. It's also, I suspect, the most useful thing in the whole project.

---

## I was wrong six times, then the checker failed too

One last thing, because I think it's the most portable lesson here.

During the hardening pass, six things I had confidently written down turned out to be false. Not typos - actual claims I'd reasoned my way to and believed. Then the final publication review found the same pattern again: a new abort class had been added but one hand-maintained result population had not. The validator caught it, but the build still went green because a shell pipeline masked the validator's failure.

They all failed the same way. Each time, I'd looked at part of the picture and written down a conclusion about the whole picture.

None of them was caught by re-reading my notes. I re-read my notes constantly. You can't catch this error by re-reading, because when you re-read you just re-convince yourself.

What caught them was the same move: **work the answer out fresh from the actual thing, then compare it to what I'd claimed.** The publication bug added one more lesson: make sure the failure of that fresh calculation actually fails the build. A checker that complains into a pipe nobody listens to is merely literature.

So if you take one thing from this that has nothing to do with AI:

> If it matters, don't re-read your notes. Recompute the answer and see if it still matches.

---

## Where this leaves things

There's one honest gap I want to name, because leaving it out would be exactly the kind of overclaiming this project set out to criticise.

I don't know how often people actually misremember what they authorised. My test cases assume it happens. It probably does - it matches ordinary experience. But nobody has measured the *rate*, and that rate is what decides whether any of this matters in the real world. It would take studying real assistants doing real work for real people.

Until someone does that, everything above is a map of what's possible, not a measurement of what's happening.

Still, the practical advice is simple enough to act on today:

**If you're using an AI assistant, ask who keeps the record.** If the answer is "the assistant does," then in any disagreement, you're each holding your own word and nothing else.

Which is precisely the problem someone solved with a stick and a knife, several hundred years ago.

---

*Tallystick is an independent research project. The technical write-up, test corpus, canonical results, and full correction record are included with the accompanying repository.*
