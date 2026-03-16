from django.db import migrations


HOW_IT_WORKS_CONTENT = """
<h3>Community Engagement Compass</h3>

<p>The Community Engagement Compass is a practical, searchable resource designed to support community members and people working in public health, health care, and community organizations in their community engagement.</p>

<p>The Compass lets you explore the <a href="https://www.healthjustice.co/NYCDOHMHCEFramework" target="_blank">New York City Department of Health and Mental Hygiene Community Engagement Framework</a>. We intend to add additional vetted frameworks and community-contributed resources over time. The Compass is not intended to replace community leadership, lived experience, or local knowledge. It is free and open to anyone.</p>

<h3>How to get started</h3>

<p>Ask the Compass questions like:</p>

<h4>FOR HEALTH PROFESSIONALS AND INSTITUTIONS</h4>

<p><strong>Understanding the framework</strong></p>
<ul>
<li>What are the four types of community engagement, and when should I use each one?</li>
<li>What principles should guide my work if I want to advance health equity?</li>
<li>What does shared leadership actually look like in practice?</li>
</ul>

<p><strong>Planning and applying the framework</strong></p>
<ul>
<li>How do I know which engagement approach fits my project timeline and resources?</li>
<li>How should I approach community engagement during an infectious disease outbreak?</li>
<li>How can I incorporate community feedback into program design decisions?</li>
</ul>

<p><strong>Building partnerships</strong></p>
<ul>
<li>How do I build trust with communities that have had negative experiences with health departments?</li>
<li>What does it mean to go to the community rather than expecting communities to come to us?</li>
<li>How do I partner with faith-based organizations in my neighborhood?</li>
<li>What are concrete ways to ensure transparency in my partnership work?</li>
</ul>

<h4>FOR COMMUNITY MEMBERS AND ORGANIZATIONS</h4>

<p><strong>Holding institutions accountable</strong></p>
<ul>
<li>What should I expect from a health organization that says it wants to partner with our community?</li>
<li>A health department says it engaged our community. What should that process have included?</li>
<li>What does the framework say shared leadership between institutions and communities actually involves?</li>
</ul>

<p><strong>Advocating for your community</strong></p>
<ul>
<li>How can our organization use this framework to advocate for more accountable engagement practices?</li>
<li>What questions should we ask when a hospital says it consulted the community?</li>
<li>What does the framework say about who should have decision-making power in a community engagement process?</li>
</ul>

<p>The Compass retrieves relevant information, shows where in the text the answer was drawn from, and includes a confidence level for the response.</p>

<h3>Data source and scope</h3>

<p>The Compass currently draws from the <a href="https://www.healthjustice.co/NYCDOHMHCEFramework" target="_blank">New York City Department of Health and Mental Hygiene Community Engagement Framework</a>. We plan to add additional vetted frameworks and community-contributed resources.</p>

<h3>Document management</h3>

<p>You can upload your own community engagement frameworks and models. After document review, the Compass can make those documents searchable. Community members and organizations are especially encouraged to contribute engagement practices, governance models, and lessons from their own experiences. These contributions will shape the knowledge base alongside institutional frameworks. You will be able to view your full list of uploads with basic details here on the My Docs page. You can remove items at any time.</p>

<h3>How answers are generated</h3>

<p>When you upload a document, the Compass splits it into readable segments and builds an index. It can find relevant passages even when your wording does not exactly match the source text. It then pulls together the passages and provides direct citations so that you can trace the information provided back to the source, along with a confidence level.</p>

<p>Every answer includes sources so you can check the original material and confirm accuracy. You can open a document and go directly to a cited section.</p>

<h3>How to use the Community Engagement Compass</h3>

<p>Start broad to scan the resource, then narrow to specific questions. Ask follow-up questions to request examples, checklists, or decision points. Use the citations to click through and skim the source to confirm that the guidance fits your context and aligns with community direction. It is also helpful to read the original source and share it and the Compass with colleagues.</p>

<h3>Privacy and security</h3>

<p>Your uploads are encrypted in transit and at rest. Your documents remain private unless you choose to share them. You can delete files at any time.</p>

<h3>Community Note</h3>

<p>True partnership asks organizations to examine their policies and assumptions about their capacity for community engagement. Communities should determine their own engagement processes, health priorities, and solutions. The Compass can support organizations in building capacity to responsibly and ethically engage with communities as accountable partners. It does not substitute for community voice, leadership, or self-determination.</p>
""".strip()


def update_how_it_works_content(apps, schema_editor):
    HowItWorksContent = apps.get_model('chat', 'HowItWorksContent')
    obj = HowItWorksContent.objects.filter(is_active=True).first()
    if obj:
        obj.content = HOW_IT_WORKS_CONTENT
        obj.save()
    else:
        HowItWorksContent.objects.create(
            title="How It Works",
            content=HOW_IT_WORKS_CONTENT,
            is_active=True,
        )


def reverse_how_it_works_content(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_update_about_content'),
    ]

    operations = [
        migrations.RunPython(update_how_it_works_content, reverse_how_it_works_content),
    ]
