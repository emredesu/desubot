import discord
from discord.ext import commands
from nh_module import *
from datetime import datetime
from nekos import img as nekosimg
import random
import re
import asyncio
import rule34 as ru34

bot = commands.Bot(command_prefix="~")
start_time = datetime.now()


def get_uptime():
	time_elapsed = (datetime.now() - start_time).seconds

	seconds = time_elapsed
	minutes = 0
	hours = 0
	days = 0

	if seconds >= 60:
		minutes += seconds // 60
		seconds = seconds % 60
	if minutes >= 60:
		hours += minutes // 60
		minutes = minutes % 60
	if hours >= 24:
		days += hours // 24
		hours = hours % 24

	return "The bot has been running for {} days, {} hours, {} minutes and {} seconds!".format(days, hours, minutes, seconds)


@bot.event
async def on_connect():
	print("{} live!".format(bot.user))


@bot.event
async def on_command_error(ctx, error):
	ignored_errors = [discord.ext.commands.CommandNotFound]

	if error in ignored_errors:
		return
	elif isinstance(error, discord.ext.commands.CommandInvokeError):
		if "DoujinshiNotFound" in str(error):  # todo: fix these to be not scuffed, error.original and error.__cause__ return None; find out why
			await ctx.send("No doujinshi with the given numbers were found. (╥﹏╥)")
		elif "NothingFound" in str(error):
			await ctx.send("Couldn't connect to the nekos.life API. (╥﹏╥)")
		else:
			print(error)
	elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
		await ctx.send("That command needed one or more arguments, but you didn't supply them. Use ~commands to see the details for all the commands. ( ◡‿◡ *)")
	else:
		print(error)


@bot.command(aliases=["test2", "aliastest"])
async def test(ctx):
	await ctx.send("Hello world! ヾ(・ω・*)")


@bot.command()
async def debug(ctx, arg):
	await ctx.send(arg)


@bot.command()
async def ping(ctx):
	await ctx.send(get_uptime())


@bot.event
async def get_doujin(ctx, arg):
	try:
		magic_numbers = int(arg)
	except ValueError:
		await ctx.send("Not a valid magic number set, magic numbers need to be numbers only. ヾ( ￣O￣)ツ")
	else:
		doujin = get_doujin_data(magic_numbers)
		name = doujin["name"]
		tags = doujin["tags"]
		page_count = doujin["page_count"]
		gallery = doujin["image_gallery"]
		doujin_cover = doujin["cover"]
		nhentai_logo = "https://i.imgur.com/uLAimaY.png"

		doujin_embed = discord.Embed(title=name, type="rich", colour=discord.Colour.from_rgb(255, 255, 0))
		doujin_embed.set_image(url=doujin_cover)
		doujin_embed.set_thumbnail(url=nhentai_logo)
		doujin_embed.add_field(name="Tags", value=(", ".join(tags)))
		doujin_embed.add_field(name="Pages", value=page_count)

		sent = await ctx.send(embed=doujin_embed)  # creating a discord.message.Message object

		reactions = ["📖", "❌"]
		"""
		📖: put the doujin into the "reading" state, give the user the ability to iterate over pages
		❌: delete the message
		"""

		for emoji in reactions:
			await discord.Message.add_reaction(sent, emoji=emoji)

		def emoji_check_for_reading(reaction, source):
			return source != bot.user and str(reaction.emoji) in reactions

		try:
			reacted, user = await bot.wait_for("reaction_add", timeout=120.0, check=emoji_check_for_reading)
		except asyncio.TimeoutError:
			for emoji in reactions:
				await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)
		else:
			if reacted.emoji == "📖":
				for emoji in reactions:
					await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)

				updated_doujin_embed = discord.Embed(title=name, type="rich", colour=discord.Colour.from_rgb(255, 255, 0))
				updated_doujin_embed.set_image(url=gallery[0])
				updated_doujin_embed.set_thumbnail(url=nhentai_logo)
				updated_doujin_embed.set_footer(text="Current page: {}/{}".format("1", page_count))

				await sent.edit(embed=updated_doujin_embed)

				valid_reactions = ["⏪", "⬅", "⏹", "➡", "⏩"]
				"""
				⏪: go to the first page
				⬅: go to the previous page, go to the last page if on the first page
				⏹: delete the message
				➡: go to the next page, go to the firstp age if on the last page
				⏩: go the the last page
				"""
				for emoji in valid_reactions:
					await discord.Message.add_reaction(sent, emoji=emoji)

				def emoji_check_during_reading(reaction, source):
					return source != bot.user and str(reaction.emoji) in valid_reactions

				async def update_embed(url, page):
					reading_embed = discord.Embed(title=name, type="rich", colour=discord.Color.from_rgb(255, 255, 0))
					reading_embed.set_image(url=url)
					updated_doujin_embed.set_thumbnail(url=nhentai_logo)
					reading_embed.set_footer(text="Current page: {}/{}".format(page, page_count))
					await sent.edit(embed=reading_embed)

				current_page = 0

				while True:
					try:
						reaction, source = await bot.wait_for("reaction_add", timeout=120.0, check=emoji_check_during_reading)
					except asyncio.TimeoutError:
						for emoji in valid_reactions:
							await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)
						break
					else:
						reacted_emoji = reaction.emoji

						if reacted_emoji == "⏪":
							current_page = 0
							await update_embed(gallery[current_page], current_page + 1)
						elif reacted_emoji == "⏩":
							current_page = gallery.index(gallery[-1])
							await update_embed(gallery[current_page], current_page + 1)
						elif reacted_emoji == "⏹":
							await discord.Message.delete(sent)
							break
						elif reacted_emoji == "⬅":
							current_page -= 1

							if current_page < 0:
								current_page = gallery.index(gallery[-1])
								await update_embed(gallery[current_page], current_page + 1)
							else:
								await update_embed(gallery[current_page], current_page + 1)
						elif reacted_emoji == "➡":
							current_page += 1

							if current_page > len(gallery) - 1:
								current_page = 0
								await update_embed(gallery[current_page], current_page + 1)
							else:
								await update_embed(gallery[current_page], current_page + 1)
			elif reacted.emoji == "❌":
				await discord.Message.delete(sent)


@bot.command(aliases=["gh", "gd", "di", "h", "d"])
async def doujin_info(ctx, arg):
	await get_doujin(ctx, arg)


@bot.command(aliases=["rd", "rh"])
async def random_doujin(ctx):
	await get_doujin(ctx, get_random_doujin())


@bot.command(aliases=["sd", "sh"])
async def search_doujin(ctx, arg):
	results = search_doujins(arg)
	nhentai_logo = "https://i.imgur.com/uLAimaY.png"

	if len(results) == 0:
		await ctx.send("No results with the search term were found. Note that you need to search with \"\" to search for multiple words. For example: ~search_doujin \"maki nico\" __φ(．．)")
	else:
		first_result = results[0]
		data = get_doujin_data(first_result)
		name = data["name"]
		tags = data["tags"]
		page_count = data["page_count"]
		doujin_cover = data["cover"]

		doujin_embed = discord.Embed(title=name, type="rich", colour=discord.Colour.from_rgb(255, 255, 0))
		doujin_embed.set_image(url=doujin_cover)
		doujin_embed.set_thumbnail(url=nhentai_logo)
		doujin_embed.add_field(name="Tags", value=(", ".join(tags)))
		doujin_embed.set_footer(text="Results: {}/{}".format(results.index(first_result) + 1, len(results)))
		doujin_embed.add_field(name="Pages", value=page_count)

		sent = await ctx.send(embed=doujin_embed)

		valid_reactions = ["⬅", "📖", "❌", "➡"]
		"""
		⬅: go to the info of the previous doujin, or the last doujin if on the first one
		➡: go to the info of the next doujin, or the first doujin if on the last one
		📖: put the current doujin into the reading state
		❌: delete the message
		"""

		for reaction in valid_reactions:
			await discord.Message.add_reaction(sent, emoji=reaction)

		def emoji_check(reaction, source):
			return source != bot.user and str(reaction.emoji) in valid_reactions

		async def update_embed(displaying, index):
			new_data = get_doujin_data(displaying)

			updated_embed = discord.Embed(title=new_data["name"], type="rich", colour=discord.Colour.from_rgb(255, 255, 0))
			updated_embed.set_image(url=new_data["cover"])
			updated_embed.set_thumbnail(url=nhentai_logo)
			updated_embed.add_field(name="Pages", value=new_data["page_count"])
			updated_embed.add_field(name="Tags", value=", ".join(new_data["tags"]))
			updated_embed.set_footer(text="Results: {}/{}".format(index, len(results)))
			await sent.edit(embed=updated_embed)

		current_doujin = 0

		while True:
			try:
				reacted, user = await bot.wait_for("reaction_add", timeout=120.0, check=emoji_check)
			except asyncio.TimeoutError:
				for emoji in valid_reactions:
					await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)
				break
			else:
				if reacted.emoji == "⬅":
					current_doujin -= 1

					if current_doujin < 0:
						current_doujin = results.index(results[-1])
						await update_embed(results[current_doujin], current_doujin + 1)
					else:
						await update_embed(results[current_doujin], current_doujin + 1)
				elif reacted.emoji == "➡":
					current_doujin += 1

					if current_doujin > len(results) - 1:
						current_doujin = 0
						await update_embed(results[current_doujin], current_doujin + 1)
					else:
						await update_embed(results[current_doujin], current_doujin + 1)
				elif reacted.emoji == "📖":
					await get_doujin(ctx, results[current_doujin])
					break
				elif reacted.emoji == "❌":
					await discord.Message.delete(sent)
					break


@bot.command()
async def owoify(ctx, args):
	faces = ["owo", "UwU", ">w<", "^w^"]
	v = args
	r = re.sub('[rl]', "w", v)
	r = re.sub('[RL]', "W", r)
	r = re.sub('ove', 'uv', r)
	r = re.sub('n', 'ny', r)
	r = re.sub('N', 'NY', r)
	r = re.sub('[!]', " " + random.choice(faces) + " ", r)
	await ctx.send(r)

available_tags = ['feet', 'yuri', 'trap', 'futanari', 'hololewd', 'lewdkemo', 'solog', 'feetg', 'cum', 'erokemo', 'les', 'wallpaper', 'lewdk', 'ngif', 'meow', 'tickle', 'lewd', 'feed', 'gecg', 'eroyuri', 'eron',
'cum_jpg', 'bj', 'nsfw_neko_gif', 'solo', 'kemonomimi', 'nsfw_avatar', 'gasm', 'poke', 'anal', 'slap', 'hentai', 'avatar', 'erofeet', 'holo', 'keta', 'blowjob', 'pussy', 'tits', 'holoero', 'lizard', 'pussy_jpg',
'pwankg', 'classic', 'kuni', 'waifu', 'pat', '8ball', 'kiss', 'femdom', 'neko', 'spank', 'cuddle', 'erok', 'fox_girl', 'boobs', 'Random_hentai_gif', 'smallboobs', 'hug', 'ero', 'random']


@bot.command()
async def nekos_tags(ctx):
	await ctx.send(", ".join(available_tags))


@bot.command()
async def nekos(ctx, arg1, arg2):
	try:
		tag = arg1
		count = int(arg2)
	except ValueError:
		await ctx.send("Invalid usage. Example usage: ~nekos hug 20")
	else:
		if tag not in available_tags:
			await ctx.send("Not an available tag. For a list of available tags, visit https://pastebin.com/YvJysxNL or use ~nekos_tags")
		elif int(count) > 50:
			await ctx.send("To avoid getting ratelimited by the nekos api, you can only get 50 images at most. (╥_╥)")
		else:
			gallery = [nekosimg(tag) for i in range(count)]

			nekos_embed = discord.Embed(description="Images with the tag \"{}\" on nekos.life".format(tag))
			nekos_embed.set_image(url=gallery[0])
			nekos_embed.set_thumbnail(url="https://nekos.life/static/icons/favicon-194x194.png")
			nekos_embed.set_footer(text="Results: {}/{}".format(1, len(gallery)))

			sent = await ctx.send(embed=nekos_embed)

			async def update_embed(img, cnt):
				new_embed = discord.Embed(description="Images with the tag \"{}\" on nekos.life".format(tag))
				new_embed.set_image(url=img)
				new_embed.set_footer(text="Results: {}/{}".format(cnt, len(gallery)))
				nekos_embed.set_thumbnail(url="https://nekos.life/static/icons/favicon-194x194.png")
				await sent.edit(embed=new_embed)

			reactions = ["⏪", "⬅", "⏹", "➡", "⏩"]
			"""
			⏪: go to the first image
			⬅: go to the previous image, or the last one if on the first
			⏹: delete the message
			➡: go to the next image, or the first one if on the last
			⏩: go to the last image
			"""

			for reaction in reactions:
				await discord.Message.add_reaction(sent, emoji=reaction)

			def check(react, source):
				return source != bot.user and str(react.emoji) in reactions

			current_image = 0

			while True:
				try:
					reacted, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
				except asyncio.TimeoutError:
					for emoji in reactions:
						await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)
					break
				else:
					if reacted.emoji == "⏪":
						current_image = 0
						await update_embed(gallery[current_image], current_image + 1)
					elif reacted.emoji == "⏩":
						current_image = gallery.index(gallery[-1])
						await update_embed(gallery[current_image], current_image + 1)
					elif reacted.emoji == "⏹":
						await discord.Message.delete(sent)
						break
					elif reacted.emoji == "⬅":
						current_image -= 1

						if current_image < 0:
							current_image = gallery.index(gallery[-1])
							await update_embed(gallery[current_image], current_image + 1)
						else:
							await update_embed(gallery[current_image], current_image + 1)
					elif reacted.emoji == "➡":
						current_image += 1

						if current_image > len(gallery) - 1:
							current_image = 0
							await update_embed(gallery[current_image], current_image + 1)
						else:
							await update_embed(gallery[current_image], current_image + 1)


@bot.command(aliases=["r34"])
async def rule34(ctx, arg):
	r34 = ru34.Rule34(bot.loop)
	gallery = await r34.getImageURLS(arg)

	if gallery is None:
		await ctx.send("No results with the search term were found. Note that you need to search with \"\" to search for multiple words. For example: ~rule34 \"touhou reimu\" __φ(．．)")
	else:
		r34_embed = discord.Embed(description="Image results for the term \"{}\" on Rule34".format(arg))
		r34_embed.set_image(url=gallery[0])
		r34_embed.set_thumbnail(url="https://i.imgur.com/Zam0Wwg.png")
		r34_embed.set_footer(text="Results: {}/{}".format(1, len(gallery)))

		sent = await ctx.send(embed=r34_embed)

		async def update_embed(url, cnt):
			updated_embed = discord.Embed(description="Image results for the term \"{}\" on Rule34".format(arg))
			updated_embed.set_image(url=url)
			updated_embed.set_thumbnail(url="https://i.imgur.com/Zam0Wwg.png")
			updated_embed.set_footer(text="Results: {}/{}".format(cnt, len(gallery)))

			await sent.edit(embed=updated_embed)

		reactions = ["⏪", "⬅", "⏹", "➡", "⏩"]
		"""
		⏪: go to the first image
		⬅: go to the previous image or the last one if on the first
		⏹: delete the message
		➡: go to the next image or the first one if on the last
		⏩: go to the last image
		"""

		for reaction in reactions:
			await discord.Message.add_reaction(sent, emoji=reaction)

		def check(react, source):
			return source != bot.user and str(react.emoji) in reactions

		current_image = 0

		while True:
			try:
				reacted, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
			except asyncio.TimeoutError:
				for emoji in reactions:
					await discord.Message.remove_reaction(sent, emoji=emoji, member=bot.user)
				break
			else:
				if reacted.emoji == "⏪":
					current_image = 0
					await update_embed(gallery[current_image], current_image + 1)
				elif reacted.emoji == "⏩":
					current_image = gallery.index(gallery[-1])
					await update_embed(gallery[current_image], current_image + 1)
				elif reacted.emoji == "⏹":
					await discord.Message.delete(sent)
					break
				elif reacted.emoji == "⬅":
					current_image -= 1

					if current_image < 0:
						current_image = gallery.index(gallery[-1])
						await update_embed(gallery[current_image], current_image + 1)
					else:
						await update_embed(gallery[current_image], current_image + 1)
				elif reacted.emoji == "➡":
					current_image += 1

					if current_image > len(gallery) - 1:
						current_image = 0
						await update_embed(gallery[current_image], current_image + 1)
					else:
						await update_embed(gallery[current_image], current_image + 1)


@bot.command()
async def commands(ctx):
	embed = discord.Embed()
	embed.add_field(name="~ping",
					value="Get uptime for the bot.", inline=False)
	embed.add_field(name="~doujin_info (magic) - aliases: ~gh, ~gd, ~di, ~h, ~d",
					value="Gets the information of the doujin with the magic numbers from nhentai.", inline=False)
	embed.add_field(name="~random_doujin - aliases: ~rd, ~rh", value="Gets a random doujinshi from nhentai.",
					inline=False)
	embed.add_field(name="~search_doujin (search term) - aliases: ~sd, ~sh",
					value="Searches nhentai with the term you've given. Note that you need to use quotation marks (\"\") to search with multiple terms. For example: ~search_doujin \"maki nico\"", inline=False)
	embed.add_field(name="~owoify", value="owoifies youw message.", inline=False)
	embed.add_field(name="~nekos (tag) (count)",
					value="Gets n images with the provided tag. n is the provided count. n can be maximum 50 to avoid getting ratelimitted.",
					inline=False)
	embed.add_field(name="~nekos_tags", value="Gets the tags that are usable on the nekos.life API.", inline=False)
	embed.add_field(name="~rule34 (search term)",
					value="Gets you images from Rule34 with the given search term. Note that you need to use quotation marks (\"\") to search for multiple words. Example: ~rule34 \"touhou youmu\"",
					inline=False)
	embed.add_field(name="Reactions",
					value="📖: Puts the current doujinshi into the reading state ❌: Deletes the message ⏪, ⬅, ⏹, ➡, ⏩: Cycles through images.",
					inline=False)
	await ctx.send(embed=embed)


token = "ehehe"
bot.run(token)
